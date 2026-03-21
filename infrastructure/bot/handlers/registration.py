from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from domain.exceptions import UserAlreadyRegisteredError, UsernameTakenError
from infrastructure.bot.dependencies import get_use_cases
from infrastructure.bot.keyboards import main_menu_keyboard

AWAITING_USERNAME = 1

WELCOME_TEXT = (
    "🔒 *TeleMask*\n"
    "─────────────────────\n"
    "A private messaging space inside Telegram.\n\n"
    "∙ No phone numbers\n"
    "∙ No profile pictures\n"
    "∙ No traces — just a username\n\n"
    "Messages are relayed anonymously. "
    "Nobody can link them back to your real account.\n"
    "─────────────────────\n"
    "Pick a username to get started.\n\n"
    "_3–20 characters · letters, numbers, underscores_"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    async with get_use_cases() as uc:
        user = await uc["user_repo"].get_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            f"👋 Welcome back, *{user.bot_username}*!",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    await update.message.reply_text("✏️  Enter your username:")
    return AWAITING_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = update.effective_user.id
    username = update.message.text.strip()

    async with get_use_cases() as uc:
        try:
            user = await uc["register_user"].execute(telegram_id, username)
            await update.message.reply_text(
                f"✅  You're in as *{user.bot_username}*\n\n"
                "Use the menu below to start chatting.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
            return ConversationHandler.END

        except ValueError as e:
            await update.message.reply_text(
                f"⚠️  {e}\n\n✏️  Try a different username:"
            )
            return AWAITING_USERNAME

        except UsernameTakenError:
            await update.message.reply_text(
                f"❌  *{username}* is already taken.\n\n✏️  Choose another:"
                , parse_mode="Markdown"
            )
            return AWAITING_USERNAME

        except UserAlreadyRegisteredError as e:
            await update.message.reply_text(str(e), reply_markup=main_menu_keyboard())
            return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Registration cancelled.")
    return ConversationHandler.END
