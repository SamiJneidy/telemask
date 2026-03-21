from telegram import Update
from telegram.ext import ContextTypes

from domain.entities.session import SessionStatus
from domain.exceptions import (
    CannotChatWithYourselfError,
    NotAParticipantError,
    PendingRequestAlreadyExistsError,
    SessionNotFoundError,
    UserNotFoundError,
)
from infrastructure.bot.dependencies import get_use_cases
from infrastructure.bot.keyboards import (
    chat_keyboard,
    chat_request_keyboard,
    contact_action_keyboard,
    delete_confirm_keyboard,
    end_chat_confirm_keyboard,
    main_menu_keyboard,
    profile_keyboard,
)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    data: str = query.data

    # ── Accept chat request ──────────────────────────────────────────────────
    if data.startswith("accept:"):
        session_id = int(data.split(":")[1])

        async with get_use_cases() as uc:
            try:
                session = await uc["handle_request"].accept(session_id, telegram_id)
                requester = await uc["user_repo"].get_by_telegram_id(session.requester_id)
                requester_username = requester.bot_username if requester else "unknown"
            except (SessionNotFoundError, NotAParticipantError) as e:
                await query.edit_message_text(f"⚠️  {e}")
                return

        await query.edit_message_text(
            f"🟢 *Connected with {requester_username}*\n\nType anything to start chatting.",
            parse_mode="Markdown",
        )
        await context.bot.send_message(
            chat_id=telegram_id,
            text=f"🔒  Now chatting with *{requester_username}*.\nEverything you send is anonymous.",
            parse_mode="Markdown",
            reply_markup=chat_keyboard(),
        )
        await context.bot.send_message(
            chat_id=session.requester_id,
            text=f"🟢 *Your request was accepted!*\n\n🔒  Now chatting with *{requester_username}*.\nEverything you send is anonymous.",
            parse_mode="Markdown",
            reply_markup=chat_keyboard(),
        )

    # ── Decline chat request ─────────────────────────────────────────────────
    elif data.startswith("decline:"):
        session_id = int(data.split(":")[1])

        async with get_use_cases() as uc:
            try:
                session = await uc["handle_request"].decline(session_id, telegram_id)
            except (SessionNotFoundError, NotAParticipantError) as e:
                await query.edit_message_text(f"⚠️  {e}")
                return

        await query.edit_message_text("❌  Request declined.")
        await context.bot.send_message(
            chat_id=session.requester_id,
            text="❌  Your chat request was declined.",
        )

    # ── Open a contact ───────────────────────────────────────────────────────
    elif data.startswith("contact:"):
        other_telegram_id = int(data.split(":")[1])

        async with get_use_cases() as uc:
            other_user = await uc["user_repo"].get_by_telegram_id(other_telegram_id)
            if not other_user:
                await query.edit_message_text("⚠️  User not found.")
                return

            active_session_id: int | None = None
            active_session = await uc["session_repo"].get_active_session_for_user(telegram_id)
            # Only count it if it's actually with this contact
            if active_session and other_telegram_id not in (active_session.requester_id, active_session.receiver_id):
                active_session = None
            if active_session:
                active_session_id = active_session.id
                await uc["switch_chat"].execute(telegram_id, active_session_id)

        other_username = other_user.bot_username
        if active_session_id is not None:
            text = (
                f"🔒 *{other_username}*\n"
                "─────────────────────\n"
                "Active chat — type to send a message."
            )
        else:
            text = (
                f"👤 *{other_username}*\n"
                "─────────────────────\n"
                "No active chat with this person."
            )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=contact_action_keyboard(other_telegram_id, other_username, active_session_id),
        )
        if active_session_id is not None:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=f"🔒  Chatting with *{other_username}*. Type to send a message.",
                parse_mode="Markdown",
                reply_markup=chat_keyboard(),
            )

    # ── Send a chat request from the contacts view ───────────────────────────
    elif data.startswith("request_chat:"):
        other_telegram_id = int(data.split(":")[1])

        async with get_use_cases() as uc:
            try:
                other_user = await uc["user_repo"].get_by_telegram_id(other_telegram_id)
                if not other_user:
                    await query.edit_message_text("⚠️  User not found.")
                    return

                session = await uc["send_chat_request"].execute(telegram_id, other_user.bot_username)
                me = await uc["user_repo"].get_by_telegram_id(telegram_id)
                my_username = me.bot_username if me else "Someone"
            except PendingRequestAlreadyExistsError:
                await query.answer("⏳  You already have a pending request to this user.", show_alert=True)
                return
            except (UserNotFoundError, CannotChatWithYourselfError) as e:
                await query.edit_message_text(f"⚠️  {e}")
                return

        await query.edit_message_text(
            f"📤 *Request sent to {other_user.bot_username}*\n"
            "─────────────────────\n"
            "Waiting for them to accept…\n\n"
            "_You'll be notified as soon as they respond._",
            parse_mode="Markdown",
        )
        await context.bot.send_message(
            chat_id=other_telegram_id,
            text=(
                "📩 *New chat request*\n"
                "─────────────────────\n"
                f"*{my_username}* wants to chat with you anonymously.\n\n"
                "Do you accept?"
            ),
            parse_mode="Markdown",
            reply_markup=chat_request_keyboard(session.id),
        )

    # ── End a chat: prompt ───────────────────────────────────────────────────
    elif data.startswith("end:"):
        session_id = int(data.split(":")[1])
        await query.edit_message_text(
            "⚠️ *End current chat?*\n"
            "─────────────────────\n"
            "This will close the conversation for both users.",
            parse_mode="Markdown",
            reply_markup=end_chat_confirm_keyboard(session_id),
        )

    # ── End a chat: confirmed ────────────────────────────────────────────────
    elif data.startswith("confirm_end:"):
        session_id = int(data.split(":")[1])

        async with get_use_cases() as uc:
            try:
                session, other_id = await uc["end_chat"].execute(telegram_id, session_id)
                other_user = await uc["user_repo"].get_by_telegram_id(other_id)
                other_username = other_user.bot_username if other_user else "unknown"
            except Exception as e:
                await query.edit_message_text(f"⚠️  {e}")
                return

        await query.edit_message_text(
            f"🔴  Ending chat with *{other_username}*...",
            parse_mode="Markdown",
        )
        await context.bot.send_message(
            chat_id=telegram_id,
            text="🔴  Chat ended.",
            reply_markup=main_menu_keyboard(),
        )
        await context.bot.send_message(
            chat_id=other_id,
            text="🔴  The other person has left the chat.",
            reply_markup=main_menu_keyboard(),
        )

    # ── End a chat: cancelled ────────────────────────────────────────────────
    elif data.startswith("cancel_end:"):
        await query.edit_message_text("✅  End chat cancelled.")

    # ── Delete account: prompt ────────────────────────────────────────────────
    elif data == "delete_account_prompt":
        await query.edit_message_text(
            "🗑  *Delete Account*\n"
            "─────────────────────\n"
            "This will permanently delete your account and all your contacts.\n\n"
            "⚠️  This action *cannot be undone*.",
            parse_mode="Markdown",
            reply_markup=delete_confirm_keyboard(),
        )

    # ── Delete account: confirmed ─────────────────────────────────────────────
    elif data == "confirm_delete":
        async with get_use_cases() as uc:
            try:
                notifiable_ids = await uc["delete_user"].execute(telegram_id)
            except Exception as e:
                await query.edit_message_text(f"⚠️  {e}")
                return

        await query.edit_message_text(
            "✅  Your account has been deleted.\n\n"
            "Send /start if you ever want to come back.",
        )
        for other_id in notifiable_ids:
            try:
                await context.bot.send_message(
                    chat_id=other_id,
                    text="🔴  The other person has left the chat.",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception:
                pass

    # ── Delete account: cancelled ─────────────────────────────────────────────
    elif data == "cancel_delete":
        async with get_use_cases() as uc:
            user = await uc["user_repo"].get_by_telegram_id(telegram_id)

        if not user:
            await query.edit_message_text("Something went wrong. Send /start to continue.")
            return

        joined = user.created_at.strftime("%b %d, %Y")
        status = "🟢  In a chat" if user.active_session_id else "⚪️  No active chat"
        await query.edit_message_text(
            f"👤 *Profile*\n"
            f"─────────────────────\n"
            f"Username:   `{user.bot_username}`\n"
            f"Status:        {status}\n"
            f"Joined:         {joined}\n"
            f"─────────────────────",
            parse_mode="Markdown",
            reply_markup=profile_keyboard(),
        )

    # ── New chat shortcut from contacts menu ─────────────────────────────────
    elif data == "new_chat":
        await query.edit_message_text(
            "Tap *🔍 New Chat* from the menu below.",
            parse_mode="Markdown",
        )
