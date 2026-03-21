import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./secret_chat.db")

# Webhook mode (see api.py) — full HTTPS URL Telegram will POST to, must match WEBHOOK_PATH
# Example: https://yourdomain.com/webhook
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL")

# Path on this server for POST (must match the path in WEBHOOK_URL)
_wp = (os.getenv("WEBHOOK_PATH", "/webhook") or "/webhook").strip()
WEBHOOK_PATH: str = _wp if _wp.startswith("/") else f"/{_wp}"

# Optional; if set, Telegram sends X-Telegram-Bot-Api-Secret-Token and we validate it
WEBHOOK_SECRET: str | None = os.getenv("WEBHOOK_SECRET")

UVICORN_PORT: int = int(os.getenv("UVICORN_PORT", "8000"))
