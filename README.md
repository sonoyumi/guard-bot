# 🛡️ Guard Bot

<p>
  <a href="https://github.com/sonoyumi/guard-bot/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sonoyumi/guard-bot/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-aiosqlite-003B57?logo=sqlite&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

**🇬🇧 [English](#en)** · **🇮🇹 [Italiano](#it)** · **🇺🇦 [Українська](#uk)** · **🇷🇺 [Русский](#ru)**

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

<a name="it"></a>

## 🇮🇹 Italiano

**[🇬🇧 English](#en)** · **🇮🇹 Italiano** · **[🇺🇦 Українська](#uk)** · **[🇷🇺 Русский](#ru)**

Un bot Telegram che protegge i gruppi da spam bot e spammer: i nuovi arrivati devono superare un captcha,
link, messaggi inoltrati e parole vietate vengono rimossi, chi fa flood viene silenziato e chi viola
ripetutamente le regole riceve avvisi e poi un silenziamento temporaneo (mute). Ogni gruppo viene
configurato dai propri amministratori, direttamente in chat.

### Funzionalità

- **Captcha per i nuovi arrivati:** il nuovo membro viene silenziato e deve premere "Non sono un bot" entro N secondi;
  altrimenti viene rimosso dal gruppo (espulso, non bannato: una persona reale può rientrare).
  I suoi messaggi vengono cancellati finché non supera il captcha; il messaggio di servizio "X si è unito" viene nascosto.
- **Filtri:** link (URL visibili, `t.me/…`, domini senza protocollo ed entità `text_link` nascoste), messaggi
  inoltrati, parole e frasi vietate (parole intere, senza distinzione tra maiuscole e minuscole).
- **Anti-flood:** più di N messaggi in T secondi → mute.
- **Avvisi → mute:** una violazione cancella il messaggio e assegna un avviso; dopo N avvisi l'utente viene
  silenziato per M minuti e il contatore riparte da zero.
- **Impostazioni per gruppo gestite dagli admin:** `/guard`, `/stop`, `/guardlog`, `/unwarn`. I comandi inviati da chi non è admin vengono cancellati in silenzio.
- **Gli admin non vengono mai toccati**, compresi gli admin anonimi e i post del canale collegato.
- **Rispettoso verso Telegram:** lo stato di admin viene messo in cache (nessuna richiesta per ogni messaggio), i permessi
  mancanti del bot vengono registrati nel log invece di farlo crashare, i nomi sono sottoposti a escaping HTML, il token non viene mai stampato.

### Comandi admin (nel gruppo)

| Comando | Cosa fa |
|---|---|
| `/guard` | Mostra le impostazioni attuali |
| `/guard links on\|off` · `forwards on\|off` · `captcha on\|off` | Attiva / disattiva i filtri |
| `/guard captcha_time 90` | Secondi a disposizione per il captcha (15–600) |
| `/guard flood 5 10` | Al massimo 5 messaggi ogni 10 secondi |
| `/guard warns 3` · `/guard mute 60` | Avvisi prima del mute · durata del mute in minuti |
| `/stop add <parola>` · `/stop del <parola>` · `/stop list` | Parole e frasi vietate |
| `/guardlog` | Ultime 10 azioni di moderazione |
| `/unwarn` (in risposta a un messaggio) | Azzera gli avvisi dell'utente e toglie il mute |

### Configurazione

1. Crea un bot con [@BotFather](https://t.me/BotFather), poi `/setprivacy` → **Disable**, così il bot vede tutti i messaggi del gruppo.
2. Avvialo:

   ```bash
   git clone https://github.com/sonoyumi/guard-bot.git
   cd guard-bot
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env        # impostare BOT_TOKEN
   guard-bot                   # oppure: python -m guard_bot
   ```

3. Aggiungi il bot a un gruppo e rendilo **amministratore** con i permessi "Elimina messaggi" e "Banna utenti".
4. Nel gruppo, un admin invia `/guard` per vedere le impostazioni.

Test: `pytest` (43 test, inclusi scenari end-to-end attraverso il vero Dispatcher di aiogram:
ingresso → captcha → superato / espulso, avvisi → mute, flood, comandi admin, parole vietate).

### Struttura del progetto

```
src/guard_bot/
├── rules.py     # filtri, modello delle impostazioni, tracker anti-flood (logica pura)
├── commands.py  # parsing di /guard e /stop (logica pura)
├── handlers.py  # captcha, comandi admin, moderazione
├── actions.py   # cancella / mute / espelli, cache degli admin
├── db.py        # impostazioni per chat, avvisi, captcha, registro azioni (SQLite)
├── texts.py     # testi dei messaggi
├── config.py    # .env
└── main.py      # assemblaggio + controllo dei captcha scaduti
```

### Autore

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), sviluppatore Python: bot Telegram, web scraping, automazione.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Ti serve un bot moderatore per la tua community? Scrivimi.

### Licenza

MIT, vedi [LICENSE](LICENSE).

---

<a name="uk"></a>

## 🇺🇦 Українська

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **🇺🇦 Українська** · **[🇷🇺 Русский](#ru)**

Telegram-бот, який захищає групи від спам-ботів і спамерів: новачки проходять капчу,
посилання, пересилання та стоп-слова видаляються, флудери отримують мут, а порушники — попередження,
а потім тимчасовий мут. Кожну групу налаштовують її адміни прямо в чаті.

### Можливості

- **Капча для новачків:** новий учасник отримує мут і має за N секунд натиснути «Я не бот»,
  інакше його видаляють із групи (кік, а не бан — жива людина зможе зайти знову). Поки капчу не пройдено,
  його повідомлення видаляються; службове «X приєднався до групи» приховується.
- **Фільтри:** посилання (видимі адреси, `t.me/…`, голі домени та приховані посилання `text_link`), переслані
  повідомлення, стоп-слова й фрази (цілими словами, без урахування регістру).
- **Антифлуд:** більше N повідомлень за T секунд → мут.
- **Попередження → мут:** порушення видаляє повідомлення й дає попередження; після N попереджень —
  мут на M хвилин, лічильник починається заново.
- **Налаштування для кожної групи окремо:** `/guard`, `/stop`, `/guardlog`, `/unwarn`. Команди не від адмінів мовчки видаляються.
- **Адмінів бот не чіпає**, зокрема анонімних адмінів і пости прив'язаного каналу.
- **Дбайливо з Telegram:** статус адміна кешується (без запиту на кожне повідомлення), брак прав у бота
  записується в лог, а не валить його, імена екрануються, токен не потрапляє в логи.

### Команди адміна (у групі)

| Команда | Що робить |
|---|---|
| `/guard` | Показати поточні налаштування |
| `/guard links on\|off` · `forwards on\|off` · `captcha on\|off` | Увімкнути / вимкнути фільтри |
| `/guard captcha_time 90` | Секунд на капчу (15–600) |
| `/guard flood 5 10` | Не більше 5 повідомлень за 10 секунд |
| `/guard warns 3` · `/guard mute 60` | Попереджень до муту · тривалість муту, хвилин |
| `/stop add <слово>` · `/stop del <слово>` · `/stop list` | Стоп-слова й фрази |
| `/guardlog` | Останні 10 дій модерації |
| `/unwarn` (у відповідь на повідомлення) | Зняти попередження й мут |

### Підключення

1. Створіть бота в [@BotFather](https://t.me/BotFather), потім `/setprivacy` → **Disable**, щоб бот бачив усі повідомлення групи.
2. Запустіть:

   ```bash
   git clone https://github.com/sonoyumi/guard-bot.git
   cd guard-bot
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env        # вписати BOT_TOKEN
   guard-bot                   # або: python -m guard_bot
   ```

3. Додайте бота до групи й зробіть його **адміном** із правами «Видаляти повідомлення» та «Блокувати користувачів».
4. У групі адмін пише `/guard` — з'являться налаштування.

Тести: `pytest` (43 тести, зокрема наскрізні сценарії через справжній Dispatcher aiogram:
вхід → капча → пройшов / кік, попередження → мут, флуд, команди адміна, стоп-слова).

### Структура проєкту

```
src/guard_bot/
├── rules.py     # фільтри, модель налаштувань, антифлуд (чиста логіка)
├── commands.py  # розбір /guard і /stop (чиста логіка)
├── handlers.py  # капча, команди адміна, модерація
├── actions.py   # видалити / мут / кік, кеш адмінів
├── db.py        # налаштування чатів, попередження, капчі, журнал дій (SQLite)
├── texts.py     # тексти повідомлень
├── config.py    # .env
└── main.py      # збирання + перевірка прострочених капч
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-розробник: Telegram-боти, парсинг, автоматизація.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Потрібен бот-модератор для вашої спільноти? Напишіть мені.

### Ліцензія

MIT — див. [LICENSE](LICENSE).

---

<a name="ru"></a>

## 🇷🇺 Русский

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **[🇺🇦 Українська](#uk)** · **🇷🇺 Русский**

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
