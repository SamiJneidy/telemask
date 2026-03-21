from abc import ABC, abstractmethod

from domain.entities.session import ChatSession, SessionStatus


class SessionRepository(ABC):

    @abstractmethod
    async def get_by_id(self, session_id: int) -> ChatSession | None:
        ...

    @abstractmethod
    async def get_active_session_for_user(self, telegram_id: int) -> ChatSession | None:
        """Return the single ACTIVE session for the user, or None."""
        ...

    @abstractmethod
    async def get_sessions_for_user(self, telegram_id: int) -> list[ChatSession]:
        """Return all ACTIVE and ENDED sessions where the user is a participant."""
        ...

    @abstractmethod
    async def get_pending_between(self, requester_id: int, receiver_id: int) -> ChatSession | None:
        """Return a PENDING session between two users if one exists."""
        ...

    @abstractmethod
    async def save(self, session: ChatSession) -> ChatSession:
        """Insert or update a session. Returns the saved ChatSession."""
        ...

    @abstractmethod
    async def update_status(self, session_id: int, status: SessionStatus) -> None:
        ...

    @abstractmethod
    async def delete_all_for_user(self, telegram_id: int) -> list[int]:
        """Delete all sessions for a user. Returns telegram_ids of active-session partners to notify."""
        ...
