# 🛡️ Guard Bot

<p>
  <a href="https://github.com/sonoyumi/guard-bot/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sonoyumi/guard-bot/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-aiosqlite-003B57?logo=sqlite&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

**🇬🇧 [English](#en)** · **🇷🇺 [Русский](#ru)**

---

<a name="en"></a>

## 🇬🇧 English

A Telegram bot that protects groups from spam bots and spammers: newcomers must pass a captcha,
links, forwards and stop-words are removed, flooders are muted, and repeat offenders get warnings
and then a temporary mute. Each group is configured by its own admins, right in the chat.

### Features

- **Captcha for newcomers:** a new member is muted and must press "I'm not a bot" within N seconds;
  otherwise they are removed from the group (kicked, not banned — a real person can join again).
  Their messages are deleted until the captcha is passed; the "X joined" service message is hidden.
- **Filters:** links (visible URLs, `t.me/…`, bare domains and hidden `text_link` entities), forwarded
  messages, stop-words and phrases (whole words, case-insensitive).
- **Anti-flood:** more than N messages in T seconds → mute.
- **Warnings → mute:** a violation deletes the message and gives a warning; after N warnings the user is
  muted for M minutes and the counter starts over.
- **Per-group settings by admins:** `/guard`, `/stop`, `/guardlog`, `/unwarn`. Commands from non-admins are silently deleted.
- **Admins are never touched**, including anonymous admins and posts from the linked channel.
- **Careful with Telegram:** admin status is cached (no request per message), missing bot rights are
  logged instead of crashing, names are HTML-escaped, the token is never printed.

### Admin commands (in the group)

| Command | What it does |
|---|---|
| `/guard` | Show current settings |
| `/guard links on\|off` · `forwards on\|off` · `captcha on\|off` | Toggle filters |
| `/guard captcha_time 90` | Seconds to solve the captcha (15–600) |
| `/guard flood 5 10` | At most 5 messages per 10 seconds |
| `/guard warns 3` · `/guard mute 60` | Warnings before a mute · mute length in minutes |
| `/stop add <word>` · `/stop del <word>` · `/stop list` | Stop-words and phrases |
| `/guardlog` | Last 10 moderation actions |
| `/unwarn` (as a reply) | Reset a user's warnings and unmute |

### Setup

1. Create a bot with [@BotFather](https://t.me/BotFather), then `/setprivacy` → **Disable** so the bot sees all group messages.
2. Run it:

   ```bash
   git clone https://github.com/sonoyumi/guard-bot.git
   cd guard-bot
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env        # set BOT_TOKEN
   guard-bot                   # or: python -m guard_bot
   ```

3. Add the bot to a group and make it an **admin** with "Delete messages" and "Ban users" rights.
4. In the group, an admin sends `/guard` to see the settings.

Tests: `pytest` (43 tests, including end-to-end scenarios through the real aiogram Dispatcher:
join → captcha → pass/kick, warnings → mute, flood, admin commands, stop-words).

### Project structure

```
src/guard_bot/
├── rules.py     # filters, settings model, flood tracker (pure logic)
├── commands.py  # /guard and /stop parsing (pure logic)
├── handlers.py  # captcha, admin commands, moderation
├── actions.py   # delete / mute / kick, admin cache
├── db.py        # per-chat settings, warnings, captchas, action log (SQLite)
├── texts.py     # messages
├── config.py    # .env
└── main.py      # wiring + captcha sweeper
```

### Author

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), Python developer: Telegram bots, web scraping, automation.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Need a moderator bot for your community? Get in touch.

### License

MIT, see [LICENSE](LICENSE).

---

<a name="ru"></a>

## 🇷🇺 Русский

**[🇬🇧 English](#en)** · **🇷🇺 Русский**

Telegram-бот, который защищает группы от спам-ботов и спамеров: новички проходят капчу,
ссылки, пересылки и стоп-слова удаляются, флудеры получают мут, а нарушители — предупреждения
и затем временный мут. Каждую группу настраивают её админы прямо в чате.

### Возможности

- **Капча для новичков:** новый участник получает мут и должен за N секунд нажать «Я не бот»,
  иначе его удаляют из группы (кик, а не бан — живой человек сможет зайти снова). Пока капча не пройдена,
  его сообщения удаляются; служебное «X вступил в группу» скрывается.
- **Фильтры:** ссылки (видимые адреса, `t.me/…`, голые домены и скрытые ссылки `text_link`), пересланные
  сообщения, стоп-слова и фразы (целиком, без учёта регистра).
- **Антифлуд:** больше N сообщений за T секунд → мут.
- **Предупреждения → мут:** нарушение удаляет сообщение и даёт предупреждение; после N предупреждений —
  мут на M минут, счётчик начинается заново.
- **Настройки для каждой группы:** `/guard`, `/stop`, `/guardlog`, `/unwarn`. Команды не от админов молча удаляются.
- **Админов бот не трогает**, включая анонимных админов и посты привязанного канала.
- **Аккуратно с Telegram:** статус админа кэшируется (не запрос на каждое сообщение), нехватка прав у бота
  пишется в лог, а не роняет его, имена экранируются, токен не попадает в логи.

### Команды админа (в группе)

| Команда | Что делает |
|---|---|
| `/guard` | Показать настройки |
| `/guard links on\|off` · `forwards on\|off` · `captcha on\|off` | Включить / выключить фильтры |
| `/guard captcha_time 90` | Секунд на капчу (15–600) |
| `/guard flood 5 10` | Не больше 5 сообщений за 10 секунд |
| `/guard warns 3` · `/guard mute 60` | Предупреждений до мута · длительность мута, минут |
| `/stop add <слово>` · `/stop del <слово>` · `/stop list` | Стоп-слова и фразы |
| `/guardlog` | Последние 10 действий |
| `/unwarn` (ответом) | Снять предупреждения и мут |

### Подключение

1. Создайте бота у [@BotFather](https://t.me/BotFather), затем `/setprivacy` → **Disable**, чтобы бот видел все сообщения группы.
2. Запустите:

   ```bash
   git clone https://github.com/sonoyumi/guard-bot.git
   cd guard-bot
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env        # вписать BOT_TOKEN
   guard-bot                   # или: python -m guard_bot
   ```

3. Добавьте бота в группу и сделайте **админом** с правами «Удалять сообщения» и «Блокировать пользователей».
4. В группе админ пишет `/guard` — появятся настройки.

Тесты: `pytest` (43 теста, включая сквозные сценарии через настоящий Dispatcher aiogram:
вход → капча → прошёл / кик, предупреждения → мут, флуд, команды админа, стоп-слова).

### Структура проекта

```
src/guard_bot/
├── rules.py     # фильтры, модель настроек, антифлуд (чистая логика)
├── commands.py  # разбор /guard и /stop (чистая логика)
├── handlers.py  # капча, команды админа, модерация
├── actions.py   # удалить / мут / кик, кэш админов
├── db.py        # настройки чатов, предупреждения, капчи, журнал (SQLite)
├── texts.py     # тексты
├── config.py    # .env
└── main.py      # сборка + проверка просроченных капч
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-разработчик: Telegram-боты, парсинг, автоматизация.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Нужен бот-модератор для вашего сообщества? Напишите мне.

### Лицензия

MIT — см. [LICENSE](LICENSE).
