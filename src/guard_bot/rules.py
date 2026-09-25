"""Moderation rules: pure functions, no Telegram, trivial to test."""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, replace

_LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|\b[\w-]+\.(?:com|ru|net|org|io|me|info|biz|xyz|top|online|site|shop|ua|it|de)\b)",
    re.IGNORECASE,
)
LINK_ENTITIES = {"url", "text_link"}


@dataclass(frozen=True)
class ChatSettings:
    captcha: bool = True
    captcha_seconds: int = 90
    block_links: bool = True
    block_forwards: bool = True
    stopwords: frozenset[str] = field(default_factory=frozenset)
    flood_limit: int = 5  # messages ...
    flood_seconds: int = 10  # ... per this many seconds
    warn_limit: int = 3  # warnings before a mute
    mute_minutes: int = 60

    def to_dict(self) -> dict:
        data = asdict(self)
        data["stopwords"] = sorted(self.stopwords)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> ChatSettings:
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "stopwords" in known:
            known["stopwords"] = frozenset(known["stopwords"])
        return cls(**known)

    def updated(self, **changes) -> ChatSettings:
        return replace(self, **changes)


def normalize_word(word: str) -> str:
    return " ".join(word.casefold().split())


def find_violation(
    text: str,
    entity_types: Iterable[str],
    is_forward: bool,
    settings: ChatSettings,
) -> str | None:
    """Returns a human-readable reason, or None if the message is fine."""
    if settings.block_forwards and is_forward:
        return "пересылка"
    if settings.block_links and (LINK_ENTITIES & set(entity_types) or _LINK_RE.search(text)):
        return "ссылка"
    lowered = f" {normalize_word(text)} "
    for word in sorted(settings.stopwords):
        # Whole words / phrases only: "спам" must not match "спамеров"... unless that is the stop-word.
        if re.search(rf"(?<!\w){re.escape(word)}(?!\w)", lowered):
            return f"стоп-слово «{word}»"
    return None


class FloodTracker:
    """Remembers recent message times per (chat, user) and says when the limit is exceeded."""

    def __init__(self) -> None:
        self._events: dict[tuple[int, int], deque[float]] = {}

    def hit(self, chat_id: int, user_id: int, now: float, limit: int, seconds: int) -> bool:
        events = self._events.setdefault((chat_id, user_id), deque())
        events.append(now)
        while events and now - events[0] > seconds:
            events.popleft()
        if len(events) > limit:
            events.clear()  # one mute per burst, not one per extra message
            return True
        return False

    def forget(self, chat_id: int, user_id: int) -> None:
        self._events.pop((chat_id, user_id), None)
