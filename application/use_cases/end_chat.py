from domain.entities.session import ChatSession, SessionStatus
from domain.exceptions import NoActiveSessionError, NotAParticipantError, SessionNotFoundError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class EndChat:
    def __init__(self, session_repo: SessionRepository, user_repo: UserRepository) -> None:
        self._session_repo = session_repo
        self._user_repo = user_repo

    async def execute(self, telegram_id: int, session_id: int) -> tuple[ChatSession, int]:
        """
        End a chat session. Returns (session, other_participant_telegram_id).
        """
        session = await self._session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found.")
        if telegram_id not in (session.requester_id, session.receiver_id):
            raise NotAParticipantError("You are not part of this chat.")
        if session.status != SessionStatus.ACTIVE:
            raise NoActiveSessionError("This chat is already ended.")

        await self._session_repo.update_status(session_id, SessionStatus.ENDED)

        other_id = session.other_participant(telegram_id)

        # Clear active session for both participants
        await self._user_repo.update_active_session(telegram_id, None)
        await self._user_repo.update_active_session(other_id, None)

        session.status = SessionStatus.ENDED
        return session, other_id
