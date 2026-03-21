from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.delete_user import DeleteUser
from application.use_cases.end_chat import EndChat
from application.use_cases.handle_request import HandleRequest
from application.use_cases.list_contacts import ListContacts
from application.use_cases.register_user import RegisterUser
from application.use_cases.send_chat_request import SendChatRequest
from application.use_cases.send_message import SendMessage
from application.use_cases.switch_chat import SwitchChat
from infrastructure.db.base import get_session_factory
from infrastructure.db.repositories.sql_session_repository import SqlSessionRepository
from infrastructure.db.repositories.sql_user_repository import SqlUserRepository


@asynccontextmanager
async def get_use_cases() -> AsyncGenerator[dict, None]:
    """
    Async context manager that provides all use cases wired with a single
    SQLAlchemy session. Commits on success, rolls back on error.
    """
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            user_repo = SqlUserRepository(session)
            session_repo = SqlSessionRepository(session)

            yield {
                "register_user": RegisterUser(user_repo),
                "send_chat_request": SendChatRequest(user_repo, session_repo),
                "handle_request": HandleRequest(session_repo, user_repo),
                "send_message": SendMessage(user_repo, session_repo),
                "switch_chat": SwitchChat(user_repo, session_repo),
                "end_chat": EndChat(session_repo, user_repo),
                "delete_user": DeleteUser(user_repo, session_repo),
                "list_contacts": ListContacts(session_repo, user_repo),
                "user_repo": user_repo,
                "session_repo": session_repo,
            }
