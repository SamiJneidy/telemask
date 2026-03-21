"""
CLI entrypoint: long polling (development / simple hosting).

Webhook mode (production): see infrastructure.hooks.app (or run: python server.py)
"""

import logging

from telegram.ext import Application

import config
from infrastructure.bot.telegram_app import build_application
from infrastructure.db.base import create_tables, init_db

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _setup_db(app: Application) -> None:
    """Called by PTB during initialize() — sets up DB before any updates are processed."""
    init_db(config.DATABASE_URL)
    await create_tables()
    logger.info("Database ready.")


if __name__ == "__main__":
    application = build_application(post_init=_setup_db)
    logger.info("Bot is starting (polling)...")
    application.run_polling(drop_pending_updates=True)
