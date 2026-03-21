from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from telegram import Update

import config
from infrastructure.bot.telegram_app import build_application
from infrastructure.db.base import create_tables, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not config.WEBHOOK_URL:
        raise RuntimeError(
            "WEBHOOK_URL is not set. Set it to your full HTTPS webhook URL "
            "(e.g. https://yourdomain.com/webhook). For local dev without HTTPS, use: python main.py"
        )

    init_db(config.DATABASE_URL)
    await create_tables()
    logger.info("Database ready.")

    tg_app = build_application()
    app.state.telegram_app = tg_app

    await tg_app.initialize()
    await tg_app.start()

    await tg_app.bot.set_webhook(
        url=config.WEBHOOK_URL,
        secret_token=config.WEBHOOK_SECRET,
        drop_pending_updates=True,
    )
    logger.info("Webhook registered: %s", config.WEBHOOK_URL)

    yield

    try:
        await tg_app.bot.delete_webhook(drop_pending_updates=False)
    except Exception as e:
        logger.warning("delete_webhook failed: %s", e)
    await tg_app.stop()
    await tg_app.shutdown()
    logger.info("Telegram application stopped.")


app = FastAPI(title="Telemask Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "Telemask bot webhook", "health": "/health"}


@app.post(config.WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> dict[str, bool]:
    tg_app = request.app.state.telegram_app

    if config.WEBHOOK_SECRET:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header != config.WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook secret",
            )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from None

    update = Update.de_json(data, tg_app.bot)
    if update is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse Telegram update",
        )

    try:
        await tg_app.process_update(update)
    except Exception:
        logger.exception("Unhandled error in process_update")
    return {"ok": True}


def run() -> None:
    import uvicorn

    uvicorn.run(
        "infrastructure.hooks.app:app",
        host="0.0.0.0",
        port=int(config.UVICORN_PORT),
        reload=False,
    )


if __name__ == "__main__":
    run()
