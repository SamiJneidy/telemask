from abc import ABC, abstractmethod

from domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        ...

    @abstractmethod
    async def get_by_bot_username(self, bot_username: str) -> User | None:
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Insert or update a user. Returns the saved User."""
        ...

    @abstractmethod
    async def update_active_session(self, telegram_id: int, session_id: int | None) -> None:
        ...

    @abstractmethod
    async def delete(self, telegram_id: int) -> None:
        """Permanently delete a user record."""
        ...
