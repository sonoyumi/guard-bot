"""Settings from environment variables (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(repr=False)  # never printed
    database_path: Path


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set: copy .env.example to .env and fill it in")
    path = Path(os.getenv("DATABASE_PATH", "").strip() or "data/guard.db")
    return Settings(bot_token=token, database_path=path if path.is_absolute() else PROJECT_ROOT / path)
