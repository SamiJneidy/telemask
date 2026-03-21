# TeleMask

**Chat anonymously inside Telegram** — pick a bot username (not your Telegram @), send chat requests, and relay messages without exposing your real account to the other person.

---

## Features

- **Registration** — Choose a unique username (3–20 chars, letters, numbers, underscores).
- **Chat requests** — Start a chat via `New Chat` or from **My Chats** → contact → *Chat with …*
- **Accept / decline** — The other user must approve before messaging starts.
- **One active chat** — Only one open conversation at a time.
- **Anonymous relay** — Messages are copied server-side (`copy_message`) with no "forwarded from" attribution.
- **Contacts** — Everyone you've interacted with (active + past sessions) appears in **My Chats**.
- **End chat** — With a confirmation step, from the menu or the contact view.
- **Profile & delete account** — View your username and join date; delete your account with confirmation.

---

## Tech stack

| Layer | Choice |
|---|---|
| Runtime | Python 3.11+ (3.13 tested) |
| Bot API | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 21.x |
| ORM | SQLAlchemy 2.0 (async) |
| DB (dev) | SQLite via `aiosqlite` |
| DB (prod) | PostgreSQL via `asyncpg` (drop-in — change one env var) |
| HTTP server | FastAPI + Uvicorn (webhook mode) |
| Config | python-dotenv |

### Architecture

Follows a **light DDD** layout:

- **`domain/`** — entities, repository interfaces, domain exceptions
- **`application/`** — use cases (pure business logic; no Telegram, no HTTP)
- **`infrastructure/`** — persistence (SQLAlchemy), Telegram handlers, and webhook adapter

Key infrastructure modules:

| Module | Role |
|---|---|
| `infrastructure/bot/telegram_app.py` | Wires all PTB handlers and conversations |
| `infrastructure/hooks/app.py` | FastAPI app — receives Telegram webhook POSTs |
| `infrastructure/db/` | SQLAlchemy models and repository implementations |

Database initialisation is called explicitly in each entry point (`main.py` for polling, `infrastructure/hooks/app.py` lifespan for webhooks).

---

## Prerequisites

- Python **3.11+**
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

---

## Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd "Secret Chat"
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # macOS / Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables**

   Copy `.env.example` to `.env` and fill in the values:

   ```bash
   cp .env.example .env
   ```

   Minimum required:

   ```env
   BOT_TOKEN=your_bot_token_from_botfather
   ```

   Optional (defaults shown):

   ```env
   # SQLite for local dev
   DATABASE_URL=sqlite+aiosqlite:///./secret_chat.db

   # PostgreSQL for production (add asyncpg to requirements.txt)
   # DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
   ```

   > Do **not** commit `.env`. It is already listed in `.gitignore`.

---

## Run

### Long polling — local development

```bash
python main.py
```

No public URL required. The bot calls Telegram's `getUpdates` in a loop.

### Webhooks — production (FastAPI + Uvicorn)

1. **HTTPS is required** — Telegram only POSTs to HTTPS URLs. Use a real domain + cert, or **ngrok** for testing:

   ```bash
   ngrok http 8000
   # Copy the https://... URL ngrok gives you
   ```

2. Set in `.env`:

   ```env
   WEBHOOK_URL=https://your-public-url/webhook
   WEBHOOK_PATH=/webhook          # must match the path in WEBHOOK_URL
   WEBHOOK_SECRET=some_random_string   # optional but recommended
   ```

3. Start the server:

   ```bash
   python server.py
   # or
   uvicorn server:app --host 0.0.0.0 --port 8000
   # or (full module path)
   uvicorn infrastructure.hooks.app:app --host 0.0.0.0 --port 8000
   ```

   On startup, the lifespan initialises the database and registers the webhook with Telegram. On shutdown, the webhook is deleted cleanly.

4. In production, put **nginx** (or any reverse proxy) in front of Uvicorn to handle TLS termination.

> **Note:** Use a **single** Uvicorn worker unless you add PTB persistence (e.g. `PicklePersistence`). `ConversationHandler` state is in-memory and not shared across workers.

---

## Database — switching to PostgreSQL

Only two steps:

1. Add `asyncpg` to `requirements.txt` (or `pip install asyncpg`).
2. Change `DATABASE_URL` in `.env`:

   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
   ```

No code changes needed — SQLAlchemy handles the rest.

Free PostgreSQL options: [Neon](https://neon.tech), [Supabase](https://supabase.com), [Railway](https://railway.app).

---

## Deployment (free options)

| Platform | Notes |
|---|---|
| **Railway** | Easiest — free PostgreSQL included, deploys from GitHub |
| **Render** | Free web service + PostgreSQL (free DB expires after 90 days) |
| **Fly.io** | More control, free tier, free Postgres |
| **Koyeb** | Simple GitHub deploy, no sleep on free tier |

All of these run persistent processes, which is required for long polling or webhook servers. Vercel and similar serverless platforms are **not suitable** for this bot.

---

## BotFather settings

- **`/setdescription`** — Shown when someone opens the bot for the first time.
- **`/setabouttext`** — Short line on the bot profile (tap the logo).
- **`/setcommands`** — Suggested command list:

  ```
  start - Register or open the menu
  chats - My contacts and chats
  newchat - Send a chat request by username
  profile - Your profile
  end - End the current chat
  cancel - Cancel the current step
  ```

---

## Project structure

```
.
├── main.py                    # Polling entry point
├── server.py                  # Webhook entry point (Uvicorn)
├── config.py                  # Env var loading (BOT_TOKEN, DATABASE_URL, webhook settings)
├── .env.example               # Template for .env
├── requirements.txt
│
├── domain/
│   ├── entities/              # User, ChatSession
│   ├── repositories/          # Abstract repository interfaces
│   └── exceptions.py
│
├── application/
│   └── use_cases/             # RegisterUser, SendChatRequest, SendMessage, EndChat, etc.
│
└── infrastructure/
    ├── bot/
    │   ├── telegram_app.py    # PTB Application wiring (handlers, conversations)
    │   ├── handlers/          # registration.py, chat.py, callbacks.py
    │   ├── keyboards.py
    │   └── dependencies.py
    ├── hooks/
    │   └── app.py             # FastAPI webhook adapter
    └── db/
        ├── base.py            # Engine + session factory + table creation
        ├── models/            # SQLAlchemy ORM models
        └── repositories/      # Concrete repository implementations
```

---

## Limitations & disclaimer

- This bot does **not** provide cryptographic end-to-end encryption like Telegram's native secret chats. "Anonymous" here means messages are relayed through the bot and your Telegram profile is not shown — not forensic-grade anonymity.
- Respect Telegram's [Bot API terms](https://core.telegram.org/bots/faq) and applicable laws.

---

## License

Specify your license here (e.g. MIT) or add a `LICENSE` file.
