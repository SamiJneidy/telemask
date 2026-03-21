from domain.entities.session import ChatSession, SessionStatus
from domain.exceptions import NotAParticipantError, SessionNotFoundError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class HandleRequest:
    """Accept or decline an incoming chat request."""

    def __init__(self, session_repo: SessionRepository, user_repo: UserRepository) -> None:
        self._session_repo = session_repo
        self._user_repo = user_repo

    async def accept(self, session_id: int, receiver_telegram_id: int) -> ChatSession:
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        if session.receiver_id != receiver_telegram_id:
            raise NotAParticipantError("You are not the receiver of this request.")

        await self._session_repo.update_status(session_id, SessionStatus.ACTIVE)

        # Both users enter this chat automatically
        await self._user_repo.update_active_session(session.requester_id, session_id)
        await self._user_repo.update_active_session(session.receiver_id, session_id)

        session.status = SessionStatus.ACTIVE
        return session

    async def decline(self, session_id: int, receiver_telegram_id: int) -> ChatSession:
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        if session.receiver_id != receiver_telegram_id:
            raise NotAParticipantError("You are not the receiver of this request.")

        await self._session_repo.update_status(session_id, SessionStatus.DECLINED)
        session.status = SessionStatus.DECLINED
        return session
