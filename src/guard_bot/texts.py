"""User-facing texts. Names always go through html.escape."""

from __future__ import annotations

from html import escape

from aiogram.types import User

START_PRIVATE = (
    "👋 Я охраняю Telegram-группы от спама.\n\n"
    "<b>Как подключить:</b>\n"
    "1. Добавьте меня в группу.\n"
    "2. Сделайте администратором с правами «Удалять сообщения» и «Блокировать пользователей».\n"
    "3. В группе админ может написать /guard — настройки защиты.\n\n"
    "Что умею: капча для новичков, удаление ссылок, пересылок и стоп-слов, антифлуд, "
    "предупреждения и мут, журнал действий."
)
NOT_YOUR_BUTTON = "Эта кнопка не для вас 🙂"
CAPTCHA_GONE = "Проверка уже не активна."
WELCOME = "Добро пожаловать! 👋"


def mention(user: User) -> str:
    return f'<a href="tg://user?id={user.id}">{escape(user.full_name)}</a>'


def captcha(user: User, seconds: int) -> str:
    return f"👋 {mention(user)}, добро пожаловать! Нажмите кнопку ниже в течение {seconds} секунд, чтобы писать в чат."


def warning(user: User, reason: str, count: int, limit: int) -> str:
    return f"⚠️ {mention(user)}, сообщение удалено: {escape(reason)}. Предупреждение {count}/{limit}."


def muted(user: User, reason: str, minutes: int) -> str:
    return f"🔇 {mention(user)} в муте на {minutes} мин: {escape(reason)}."
