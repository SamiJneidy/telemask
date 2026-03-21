from domain.entities.session import ChatSession, SessionStatus
from domain.exceptions import NotAParticipantError, SessionNotFoundError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class SwitchChat:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, telegram_id: int, session_id: int) -> ChatSession:
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        if session.status != SessionStatus.ACTIVE:
            raise SessionNotFoundError("This chat is no longer active.")
        if telegram_id not in (session.requester_id, session.receiver_id):
            raise NotAParticipantError("You are not part of this chat.")

        await self._user_repo.update_active_session(telegram_id, session_id)
        return session
