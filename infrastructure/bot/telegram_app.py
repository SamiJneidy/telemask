"""
Wires python-telegram-bot Application (handlers, conversations).
Infrastructure adapter: Telegram delivery layer.
"""

from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
from infrastructure.bot.handlers.callbacks import handle_callback
from infrastructure.bot.handlers.chat import (
    AWAITING_TARGET_USERNAME,
    end_chat_command,
    my_chats,
    my_profile,
    new_chat_receive_username,
    new_chat_start,
    relay_message,
)
from infrastructure.bot.handlers.registration import (
    AWAITING_USERNAME,
    cancel,
    receive_username,
    start,
)
logger = logging.getLogger(__name__)

# Filters that match reply-keyboard menu button text
MENU_TEXTS = filters.Regex(r"^(💬 My Chats|🔍 New Chat|👤 My Profile|📋 My Chats|❌ End Chat)$")


def build_application(post_init=None) -> Application:
    builder = Application.builder().token(config.BOT_TOKEN)
    if post_init is not None:
        builder = builder.post_init(post_init)
    app = builder.build()

    registration_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    new_chat_conv = ConversationHandler(
        entry_points=[
            CommandHandler("newchat", new_chat_start),
            MessageHandler(filters.Regex(r"^🔍 New Chat$"), new_chat_start),
        ],
        states={
            AWAITING_TARGET_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, new_chat_receive_username)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(registration_conv)
    app.add_handler(new_chat_conv)

    app.add_handler(MessageHandler(filters.Regex(r"^💬 My Chats$") | filters.Regex(r"^📋 My Chats$"), my_chats))
    app.add_handler(MessageHandler(filters.Regex(r"^👤 My Profile$"), my_profile))
    app.add_handler(MessageHandler(filters.Regex(r"^❌ End Chat$"), end_chat_command))

    app.add_handler(CommandHandler("chats", my_chats))
    app.add_handler(CommandHandler("end", end_chat_command))
    app.add_handler(CommandHandler("profile", my_profile))

    app.add_handler(CallbackQueryHandler(handle_callback))

    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.Sticker.ALL | filters.VOICE |
             filters.VIDEO | filters.Document.ALL | filters.AUDIO | filters.VIDEO_NOTE)
            & ~filters.COMMAND
            & ~MENU_TEXTS,
            relay_message,
        )
    )

    return app
