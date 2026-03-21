"""
Production server entry point — Telegram webhooks via FastAPI + Uvicorn.

    uvicorn server:app --host 0.0.0.0 --port 8000

For local development (no HTTPS required), use long polling:

    python main.py
"""

from infrastructure.hooks.app import app, run

__all__ = ["app"]

if __name__ == "__main__":
    run()
