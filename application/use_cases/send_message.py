from domain.exceptions import NoActiveSessionError, NotAParticipantError, SessionNotFoundError
from domain.entities.session import SessionStatus
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class SendMessage:
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, sender_telegram_id: int) -> int:
        """
        Validate the sender has an active session and return the receiver's telegram_id.
        """
        user = await self._user_repo.get_by_telegram_id(sender_telegram_id)
        if not user or user.active_session_id is None:
            raise NoActiveSessionError("You are not in an active chat. Open a chat from your contacts.")

        session = await self._session_repo.get_by_id(user.active_session_id)
        if not session:
            raise SessionNotFoundError("Active session not found.")
        if session.status != SessionStatus.ACTIVE:
            raise NoActiveSessionError("This chat is no longer active.")
        if sender_telegram_id not in (session.requester_id, session.receiver_id):
            raise NotAParticipantError("You are not a participant of this session.")

        return session.other_participant(sender_telegram_id)
