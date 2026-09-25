"""Parsing admin commands (/guard, /stop) into new settings. Pure logic."""

from __future__ import annotations

from guard_bot.rules import ChatSettings, normalize_word

GUARD_HELP = (
    "<b>Настройки</b> (только для админов):\n"
    "/guard — показать настройки\n"
    "/guard links on|off — запрет ссылок\n"
    "/guard forwards on|off — запрет пересылок\n"
    "/guard captcha on|off — капча для новичков\n"
    "/guard captcha_time 90 — секунд на капчу (15–600)\n"
    "/guard flood 5 10 — не больше 5 сообщений за 10 секунд\n"
    "/guard warns 3 — предупреждений до мута\n"
    "/guard mute 60 — длительность мута, минут\n"
    "/stop add слово · /stop del слово · /stop list — стоп-слова\n"
    "/guardlog — последние действия · /unwarn (ответом) — снять предупреждения"
)

_SWITCHES = {"links": "block_links", "forwards": "block_forwards", "captcha": "captcha"}


def _on(flag: bool) -> str:
    return "✅" if flag else "❌"


def describe(settings: ChatSettings) -> str:
    return (
        "<b>Настройки защиты</b>\n"
        f"{_on(settings.captcha)} Капча для новичков ({settings.captcha_seconds} с)\n"
        f"{_on(settings.block_links)} Запрет ссылок\n"
        f"{_on(settings.block_forwards)} Запрет пересылок\n"
        f"🌊 Флуд: не больше {settings.flood_limit} сообщений за {settings.flood_seconds} с\n"
        f"⚠️ Мут после {settings.warn_limit} предупреждений на {settings.mute_minutes} мин\n"
        f"🚫 Стоп-слов: {len(settings.stopwords)}\n\n"
        "Изменить: /guard help"
    )


def _int(value: str, low: int, high: int, what: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise ValueError(f"{what}: нужно число") from None
    if not low <= number <= high:
        raise ValueError(f"{what}: от {low} до {high}")
    return number


def apply_guard_args(settings: ChatSettings, args: list[str]) -> tuple[ChatSettings, str]:
    """/guard <key> <value...> -> (new settings, confirmation). Raises ValueError with a readable message."""
    if not args or args[0] == "help":
        return settings, GUARD_HELP
    key, values = args[0].lower(), args[1:]

    if key in _SWITCHES:
        if values not in (["on"], ["off"]):
            raise ValueError(f"Используйте: /guard {key} on|off")
        enabled = values == ["on"]
        return settings.updated(**{_SWITCHES[key]: enabled}), f"{key}: {'включено' if enabled else 'выключено'}"
    if key == "captcha_time" and len(values) == 1:
        seconds = _int(values[0], 15, 600, "Время капчи")
        return settings.updated(captcha_seconds=seconds), f"Время на капчу: {seconds} с"
    if key == "flood" and len(values) == 2:
        limit = _int(values[0], 2, 50, "Сообщений")
        seconds = _int(values[1], 1, 600, "Секунд")
        return settings.updated(flood_limit=limit, flood_seconds=seconds), f"Флуд: {limit} сообщений за {seconds} с"
    if key == "warns" and len(values) == 1:
        limit = _int(values[0], 1, 20, "Предупреждений")
        return settings.updated(warn_limit=limit), f"Мут после {limit} предупреждений"
    if key == "mute" and len(values) == 1:
        minutes = _int(values[0], 1, 60 * 24 * 7, "Минут")
        return settings.updated(mute_minutes=minutes), f"Мут на {minutes} мин"
    raise ValueError("Не понял команду. Список: /guard help")


def apply_stop_args(settings: ChatSettings, args: list[str]) -> tuple[ChatSettings, str]:
    """/stop add|del <word or phrase> | /stop list"""
    if not args or args[0] == "list":
        words = sorted(settings.stopwords)
        return settings, ("Стоп-слова: " + ", ".join(words)) if words else "Стоп-слов нет. Добавить: /stop add слово"
    action, word = args[0].lower(), normalize_word(" ".join(args[1:]))
    if action not in ("add", "del") or not word:
        raise ValueError("Используйте: /stop add слово, /stop del слово, /stop list")
    if len(word) > 64:
        raise ValueError("Слишком длинное стоп-слово (до 64 символов)")
    if action == "add":
        return settings.updated(stopwords=settings.stopwords | {word}), f"Добавлено стоп-слово «{word}»"
    if word not in settings.stopwords:
        raise ValueError(f"Стоп-слова «{word}» нет в списке")
    return settings.updated(stopwords=settings.stopwords - {word}), f"Удалено стоп-слово «{word}»"
