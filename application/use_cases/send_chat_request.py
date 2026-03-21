from datetime import datetime

from domain.entities.session import ChatSession, SessionStatus
from domain.exceptions import (
    CannotChatWithYourselfError,
    PendingRequestAlreadyExistsError,
    UserNotFoundError,
)
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class SendChatRequest:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, requester_telegram_id: int, target_bot_username: str) -> ChatSession:
        requester = await self._user_repo.get_by_telegram_id(requester_telegram_id)
        if not requester:
            raise UserNotFoundError("You are not registered. Use /start to register first.")

        target = await self._user_repo.get_by_bot_username(target_bot_username)
        if not target:
            raise UserNotFoundError(f"No user found with username '{target_bot_username}'.")

        if target.telegram_id == requester_telegram_id:
            raise CannotChatWithYourselfError("You cannot start a chat with yourself.")

        pending = await self._session_repo.get_pending_between(
            requester_telegram_id, target.telegram_id
        )
        if pending:
            raise PendingRequestAlreadyExistsError(
                f"You already have a pending request to '{target_bot_username}'."
            )

        session = ChatSession(
            id=0,
            requester_id=requester_telegram_id,
            receiver_id=target.telegram_id,
            status=SessionStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        saved = await self._session_repo.save(session)
        return saved
