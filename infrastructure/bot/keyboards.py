from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


# ── Persistent reply keyboards ───────────────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["💬 My Chats", "🔍 New Chat"], ["👤 My Profile"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["📋 My Chats", "❌ End Chat"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# ── Inline keyboards ─────────────────────────────────────────────────────────

def chat_request_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"accept:{session_id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"decline:{session_id}"),
    ]])


def contacts_keyboard(contacts: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """contacts: list of (other_telegram_id, bot_username)"""
    buttons = [
        [InlineKeyboardButton(f"👤  {username}", callback_data=f"contact:{other_id}")]
        for other_id, username in contacts
    ]
    buttons.append([InlineKeyboardButton("＋  New Chat", callback_data="new_chat")])
    return InlineKeyboardMarkup(buttons)


def contact_action_keyboard(
    other_telegram_id: int,
    other_username: str,
    active_session_id: int | None,
) -> InlineKeyboardMarkup:
    if active_session_id is not None:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔴  End Chat", callback_data=f"end:{active_session_id}")
        ]])
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"💬  Chat with {other_username}", callback_data=f"request_chat:{other_telegram_id}")
    ]])


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑  Delete Account", callback_data="delete_account_prompt")
    ]])


def delete_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑  Yes, delete permanently", callback_data="confirm_delete"),
        InlineKeyboardButton("↩️  Cancel", callback_data="cancel_delete"),
    ]])


def end_chat_confirm_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔴  Yes, end chat", callback_data=f"confirm_end:{session_id}"),
        InlineKeyboardButton("↩️  Cancel", callback_data=f"cancel_end:{session_id}"),
    ]])
