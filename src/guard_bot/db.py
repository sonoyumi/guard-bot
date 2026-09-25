"""SQLite storage: per-chat settings, warnings, pending captchas, action log."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from guard_bot.rules import ChatSettings

SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_settings (
    chat_id  INTEGER PRIMARY KEY,
    data     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS warnings (
    chat_id  INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    count    INTEGER NOT NULL,
    PRIMARY KEY (chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS captchas (
    chat_id     INTEGER NOT NULL,
    user_id     INTEGER NOT NULL,
    message_id  INTEGER NOT NULL,
    expires_at  REAL    NOT NULL,   -- unix time
    PRIMARY KEY (chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS actions (
    id         INTEGER PRIMARY KEY,
    chat_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    user_name  TEXT    NOT NULL,
    action     TEXT    NOT NULL,
    reason     TEXT    NOT NULL,
    at         TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_actions_chat ON actions (chat_id, id);
"""


@dataclass(frozen=True)
class Captcha:
    chat_id: int
    user_id: int
    message_id: int
    expires_at: float


@dataclass(frozen=True)
class Action:
    user_id: int
    user_name: str
    action: str
    reason: str
    at: datetime


class Database:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @classmethod
    async def open(cls, path: Path | str) -> Database:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.executescript(SCHEMA)
        await conn.commit()
        return cls(conn)

    async def close(self) -> None:
        await self._conn.close()

    # --- settings ---

    async def get_settings(self, chat_id: int) -> ChatSettings:
        async with self._conn.execute("SELECT data FROM chat_settings WHERE chat_id = ?", (chat_id,)) as cur:
            row = await cur.fetchone()
        return ChatSettings.from_dict(json.loads(row["data"])) if row else ChatSettings()

    async def save_settings(self, chat_id: int, settings: ChatSettings) -> None:
        await self._conn.execute(
            "INSERT INTO chat_settings (chat_id, data) VALUES (?, ?) "
            "ON CONFLICT (chat_id) DO UPDATE SET data = excluded.data",
            (chat_id, json.dumps(settings.to_dict(), ensure_ascii=False)),
        )
        await self._conn.commit()

    # --- warnings ---

    async def add_warning(self, chat_id: int, user_id: int) -> int:
        """Increments and returns the user's warning count in this chat."""
        await self._conn.execute(
            "INSERT INTO warnings (chat_id, user_id, count) VALUES (?, ?, 1) "
            "ON CONFLICT (chat_id, user_id) DO UPDATE SET count = count + 1",
            (chat_id, user_id),
        )
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT count FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)
        ) as cur:
            row = await cur.fetchone()
        return int(row["count"])

    async def reset_warnings(self, chat_id: int, user_id: int) -> None:
        await self._conn.execute("DELETE FROM warnings WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        await self._conn.commit()

    # --- captchas ---

    async def add_captcha(self, captcha: Captcha) -> None:
        await self._conn.execute(
            "INSERT OR REPLACE INTO captchas (chat_id, user_id, message_id, expires_at) VALUES (?, ?, ?, ?)",
            (captcha.chat_id, captcha.user_id, captcha.message_id, captcha.expires_at),
        )
        await self._conn.commit()

    async def pop_captcha(self, chat_id: int, user_id: int) -> Captcha | None:
        async with self._conn.execute(
            "SELECT * FROM captchas WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        await self._conn.execute("DELETE FROM captchas WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        await self._conn.commit()
        return Captcha(row["chat_id"], row["user_id"], row["message_id"], row["expires_at"])

    async def has_captcha(self, chat_id: int, user_id: int) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM captchas WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)
        ) as cur:
            return await cur.fetchone() is not None

    async def expired_captchas(self, now: float) -> list[Captcha]:
        async with self._conn.execute("SELECT * FROM captchas WHERE expires_at <= ?", (now,)) as cur:
            return [Captcha(r["chat_id"], r["user_id"], r["message_id"], r["expires_at"]) async for r in cur]

    # --- action log ---

    async def log(self, chat_id: int, user_id: int, user_name: str, action: str, reason: str) -> None:
        await self._conn.execute(
            "INSERT INTO actions (chat_id, user_id, user_name, action, reason, at) VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, user_name, action, reason, datetime.now(UTC).isoformat()),
        )
        await self._conn.commit()

    async def recent_actions(self, chat_id: int, limit: int = 10) -> list[Action]:
        async with self._conn.execute(
            "SELECT * FROM actions WHERE chat_id = ? ORDER BY id DESC LIMIT ?", (chat_id, limit)
        ) as cur:
            return [
                Action(r["user_id"], r["user_name"], r["action"], r["reason"], datetime.fromisoformat(r["at"]))
                async for r in cur
            ]
