"""Telegram handlers: captcha for newcomers, admin commands, message moderation."""

from __future__ import annotations

import asyncio
import logging
import time
from html import escape

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from guard_bot import actions, texts
from guard_bot.commands import apply_guard_args, apply_stop_args, describe
from guard_bot.db import Captcha, Database
from guard_bot.rules import FloodTracker, find_violation

logger = logging.getLogger(__name__)

router = Router()
IN_GROUP = F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})


class CaptchaCb(CallbackData, prefix="cap"):
    user_id: int


def captcha_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Я не бот", callback_data=CaptchaCb(user_id=user_id))
    return kb.as_markup()


# --- private chat ------------------------------------------------------------------------------


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def start_private(message: Message) -> None:
    await message.answer(texts.START_PRIVATE)


# --- captcha -----------------------------------------------------------------------------------


@router.message(IN_GROUP, F.new_chat_members)
async def on_join(message: Message, bot: Bot, db: Database) -> None:
    settings = await db.get_settings(message.chat.id)
    if not settings.captcha:
        return
    for member in message.new_chat_members or []:
        if member.is_bot:
            continue
        if not await actions.mute(bot, message.chat.id, member.id):
            continue  # no rights: better no captcha than a captcha that cannot be enforced
        sent = await message.answer(texts.captcha(member, settings.captcha_seconds), reply_markup=captcha_kb(member.id))
        await db.add_captcha(
            Captcha(message.chat.id, member.id, sent.message_id, time.time() + settings.captcha_seconds)
        )
    await actions.delete(bot, message.chat.id, message.message_id)  # hide the "X joined" service message


@router.callback_query(CaptchaCb.filter())
async def on_captcha(callback: CallbackQuery, callback_data: CaptchaCb, bot: Bot, db: Database) -> None:
    if callback.from_user.id != callback_data.user_id:
        await callback.answer(texts.NOT_YOUR_BUTTON, show_alert=True)
        return
    if callback.message is None:
        await callback.answer(texts.CAPTCHA_GONE)
        return
    chat_id = callback.message.chat.id
    captcha = await db.pop_captcha(chat_id, callback.from_user.id)
    if captcha is None:
        await callback.answer(texts.CAPTCHA_GONE, show_alert=True)
        return
    await actions.unmute(bot, chat_id, callback.from_user.id)
    await actions.delete(bot, chat_id, captcha.message_id)
    await callback.answer(texts.WELCOME)
    await db.log(chat_id, callback.from_user.id, callback.from_user.full_name, "captcha_ok", "прошёл капчу")


async def sweep_captchas(bot: Bot, db: Database, now: float) -> int:
    """Kicks everyone whose captcha expired; returns how many."""
    expired = await db.expired_captchas(now)
    for captcha in expired:
        await db.pop_captcha(captcha.chat_id, captcha.user_id)
        await actions.kick(bot, captcha.chat_id, captcha.user_id)
        await actions.delete(bot, captcha.chat_id, captcha.message_id)
        await db.log(captcha.chat_id, captcha.user_id, str(captcha.user_id), "kick", "не прошёл капчу")
    return len(expired)


async def captcha_loop(bot: Bot, db: Database, interval: float = 5) -> None:
    while True:
        try:
            await sweep_captchas(bot, db, time.time())
        except Exception:  # the loop must survive any single failure
            logger.exception("Captcha sweep failed")
        await asyncio.sleep(interval)


# --- admin commands (registered before the catch-all moderation handler) -----------------------


async def _admin_only(message: Message, bot: Bot, admins: actions.AdminCache) -> bool:
    if message.from_user and await admins.is_admin(bot, message.chat.id, message.from_user.id):
        return True
    await actions.delete(bot, message.chat.id, message.message_id)  # silently drop commands from non-admins
    return False


@router.message(IN_GROUP, Command("guard"))
async def cmd_guard(message: Message, command: CommandObject, bot: Bot, db: Database, admins: actions.AdminCache):
    if not await _admin_only(message, bot, admins):
        return
    settings = await db.get_settings(message.chat.id)
    args = (command.args or "").split()
    if not args:
        await message.reply(describe(settings))
        return
    try:
        new_settings, reply = apply_guard_args(settings, args)
    except ValueError as exc:
        await message.reply(escape(str(exc)))
        return
    if new_settings != settings:
        await db.save_settings(message.chat.id, new_settings)
    await message.reply(reply)


@router.message(IN_GROUP, Command("stop"))
async def cmd_stop(message: Message, command: CommandObject, bot: Bot, db: Database, admins: actions.AdminCache):
    if not await _admin_only(message, bot, admins):
        return
    settings = await db.get_settings(message.chat.id)
    try:
        new_settings, reply = apply_stop_args(settings, (command.args or "").split())
    except ValueError as exc:
        await message.reply(escape(str(exc)))
        return
    if new_settings != settings:
        await db.save_settings(message.chat.id, new_settings)
    await message.reply(escape(reply))


@router.message(IN_GROUP, Command("guardlog"))
async def cmd_log(message: Message, bot: Bot, db: Database, admins: actions.AdminCache) -> None:
    if not await _admin_only(message, bot, admins):
        return
    records = await db.recent_actions(message.chat.id)
    if not records:
        await message.reply("Журнал пуст.")
        return
    lines = [f"{r.at:%d.%m %H:%M} · {r.action} · {escape(r.user_name)} — {escape(r.reason)}" for r in records]
    await message.reply("<b>Последние действия:</b>\n" + "\n".join(lines))


@router.message(IN_GROUP, Command("unwarn"))
async def cmd_unwarn(message: Message, bot: Bot, db: Database, admins: actions.AdminCache) -> None:
    if not await _admin_only(message, bot, admins):
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if target is None:
        await message.reply("Ответьте этой командой на сообщение пользователя.")
        return
    await db.reset_warnings(message.chat.id, target.id)
    await actions.unmute(bot, message.chat.id, target.id)
    await db.log(message.chat.id, target.id, target.full_name, "unwarn", "админ снял предупреждения")
    await message.reply(f"Предупреждения сняты: {texts.mention(target)}")


# --- moderation (catch-all for group messages) -------------------------------------------------


async def _punish(message: Message, bot: Bot, db: Database, reason: str, mute_minutes: int, warn_limit: int):
    user = message.from_user
    assert user is not None
    chat_id = message.chat.id
    await actions.delete(bot, chat_id, message.message_id)
    count = await db.add_warning(chat_id, user.id)
    if count >= warn_limit:
        await db.reset_warnings(chat_id, user.id)
        await actions.mute(bot, chat_id, user.id, mute_minutes)
        await db.log(chat_id, user.id, user.full_name, "mute", reason)
        await message.answer(texts.muted(user, reason, mute_minutes))
    else:
        await db.log(chat_id, user.id, user.full_name, "warn", reason)
        await message.answer(texts.warning(user, reason, count, warn_limit))


@router.message(IN_GROUP)
async def moderate(message: Message, bot: Bot, db: Database, admins: actions.AdminCache, flood: FloodTracker):
    user = message.from_user
    if user is None or user.is_bot or message.is_automatic_forward:
        return
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return  # anonymous admin
    chat_id = message.chat.id
    if await admins.is_admin(bot, chat_id, user.id):
        return
    if await db.has_captcha(chat_id, user.id):
        await actions.delete(bot, chat_id, message.message_id)
        return

    settings = await db.get_settings(chat_id)
    if flood.hit(chat_id, user.id, time.monotonic(), settings.flood_limit, settings.flood_seconds):
        await actions.delete(bot, chat_id, message.message_id)
        await actions.mute(bot, chat_id, user.id, settings.mute_minutes)
        await db.log(chat_id, user.id, user.full_name, "mute", "флуд")
        await message.answer(texts.muted(user, "флуд", settings.mute_minutes))
        return

    entities = (message.entities or []) + (message.caption_entities or [])
    reason = find_violation(
        message.text or message.caption or "",
        (e.type for e in entities),
        message.forward_origin is not None,
        settings,
    )
    if reason:
        await _punish(message, bot, db, reason, settings.mute_minutes, settings.warn_limit)
