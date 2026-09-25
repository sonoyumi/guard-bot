"""Moderator actions and the admin cache. Every Telegram call tolerates missing rights."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatPermissions

logger = logging.getLogger(__name__)

MUTED = ChatPermissions(can_send_messages=False)
ALLOWED = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)
_TELEGRAM_ERRORS = (TelegramBadRequest, TelegramForbiddenError)


async def delete(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.delete_message(chat_id, message_id)
    except _TELEGRAM_ERRORS as exc:  # already deleted, too old, or no rights
        logger.info("Cannot delete message %s in %s: %s", message_id, chat_id, exc)


async def mute(bot: Bot, chat_id: int, user_id: int, minutes: int | None = None) -> bool:
    until = timedelta(minutes=minutes) if minutes else None  # None = until unmuted (captcha)
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=MUTED, until_date=until)
        return True
    except _TELEGRAM_ERRORS as exc:
        logger.warning("Cannot mute %s in %s (is the bot an admin with 'Ban users'?): %s", user_id, chat_id, exc)
        return False


async def unmute(bot: Bot, chat_id: int, user_id: int) -> None:
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions=ALLOWED)
    except _TELEGRAM_ERRORS as exc:
        logger.warning("Cannot unmute %s in %s: %s", user_id, chat_id, exc)


async def kick(bot: Bot, chat_id: int, user_id: int) -> None:
    """Removes the user but lets them join again later (ban + unban)."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    except _TELEGRAM_ERRORS as exc:
        logger.warning("Cannot kick %s from %s: %s", user_id, chat_id, exc)


class AdminCache:
    """Asking Telegram 'is this user an admin?' on every message would hit rate limits, so answers are cached."""

    def __init__(self, ttl: float = 300) -> None:
        self._ttl = ttl
        self._cache: dict[tuple[int, int], tuple[bool, float]] = {}

    async def is_admin(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        now = time.monotonic()
        cached = self._cache.get((chat_id, user_id))
        if cached and now - cached[1] < self._ttl:
            return cached[0]
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            result = member.status in ("administrator", "creator")
        except _TELEGRAM_ERRORS:
            result = False
        self._cache[(chat_id, user_id)] = (result, now)
        return result
