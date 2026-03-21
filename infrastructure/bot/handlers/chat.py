from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from domain.exceptions import (
    CannotChatWithYourselfError,
    NoActiveSessionError,
    PendingRequestAlreadyExistsError,
    UserNotFoundError,
)
from infrastructure.bot.dependencies import get_use_cases
from infrastructure.bot.keyboards import (
    chat_keyboard,
    chat_request_keyboard,
    contacts_keyboard,
    end_chat_confirm_keyboard,
    main_menu_keyboard,
    profile_keyboard,
)

AWAITING_TARGET_USERNAME = 10


async def my_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)
        if not user:
            await update.message.reply_text(
                "You're not registered yet. Send /start to create an account."
            )
            return
        contacts = await uc["list_contacts"].execute(telegram_id)

    if not contacts:
        await update.message.reply_text(
            "💬 *My Chats*\n"
            "─────────────────────\n"
            "No contacts yet.\n\n"
            "Tap *🔍 New Chat* to send your first request.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        "💬 *My Chats*\n─────────────────────\nTap a contact to open:",
        parse_mode="Markdown",
        reply_markup=contacts_keyboard(contacts),
    )


async def new_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id

    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text(
            "You're not registered yet. Send /start to create an account."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 *New Chat*\n"
        "─────────────────────\n"
        "Enter the username of the person you want to connect with:",
        parse_mode="Markdown",
    )
    return AWAITING_TARGET_USERNAME


async def new_chat_receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    target_username = update.message.text.strip()

    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)
        # If the user already has an active session, this text is likely a chat message,
        # not a username for a new request. Relay it and exit the conversation state.
        if user and user.active_session_id is not None:
            await relay_message(update, context)
            return ConversationHandler.END

        try:
            session = await uc["send_chat_request"].execute(telegram_id, target_username)
            requester = await uc["user_repo"].get_by_telegram_id(telegram_id)

            await update.message.reply_text(
                f"📤  Request sent to *{target_username}*\n\nWaiting for them to accept…",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )

            await context.bot.send_message(
                chat_id=session.receiver_id,
                text=(
                    "📩 *New chat request*\n"
                    "─────────────────────\n"
                    f"*{requester.bot_username}* wants to chat with you anonymously.\n\n"
                    "Do you accept?"
                ),
                parse_mode="Markdown",
                reply_markup=chat_request_keyboard(session.id),
            )
            return ConversationHandler.END

        except UserNotFoundError as e:
            await update.message.reply_text(f"❌  {e}")
            return ConversationHandler.END
        except CannotChatWithYourselfError:
            await update.message.reply_text("⚠️  You can't send a request to yourself.")
            return ConversationHandler.END
        except PendingRequestAlreadyExistsError:
            await update.message.reply_text(
                f"⏳  You already have a pending request to *{target_username}*.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END


async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Relay any text or media message to the other participant in the active chat."""
    telegram_id = update.effective_user.id
    msg = update.message

    async with get_use_cases() as uc:
        try:
            receiver_id = await uc["send_message"].execute(sender_telegram_id=telegram_id)
        except NoActiveSessionError as e:
            await msg.reply_text(f"⚠️  {e}", reply_markup=main_menu_keyboard())
            return
        except Exception as e:
            await msg.reply_text(
                f"⚠️  Could not send message: {type(e).__name__}",
                reply_markup=main_menu_keyboard(),
            )
            return

    try:
        await context.bot.copy_message(
            chat_id=receiver_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )
    except Exception as e:
        await msg.reply_text(f"⚠️  Delivery failed: {e}")


async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)
        if not user or user.active_session_id is None:
            await update.message.reply_text(
                "You're not in an active chat.",
                reply_markup=main_menu_keyboard(),
            )
            return

    await update.message.reply_text(
        "⚠️ *End current chat?*\n"
        "─────────────────────\n"
        "This will close the conversation for both users.",
        parse_mode="Markdown",
        reply_markup=end_chat_confirm_keyboard(user.active_session_id),
    )


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text(
            "You're not registered yet. Send /start to create an account."
        )
        return

    joined = user.created_at.strftime("%b %d, %Y")
    status = "🟢  In a chat" if user.active_session_id else "⚪️  No active chat"

    await update.message.reply_text(
        f"👤 *Profile*\n"
        f"─────────────────────\n"
        f"Username:   `{user.bot_username}`\n"
        f"Status:        {status}\n"
        f"Joined:         {joined}\n"
        f"─────────────────────",
        parse_mode="Markdown",
        reply_markup=profile_keyboard(),
    )
