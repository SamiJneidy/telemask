from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from infrastructure.db.models import UserModel


class SqlUserRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.telegram_id == telegram_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_bot_username(self, bot_username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.bot_username == bot_username.lower())
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save(self, user: User) -> User:
        existing = await self._session.get(UserModel, user.telegram_id)
        if existing:
            existing.bot_username = user.bot_username.lower()
            existing.active_session_id = user.active_session_id
        else:
            existing = UserModel(
                telegram_id=user.telegram_id,
                bot_username=user.bot_username.lower(),
                active_session_id=user.active_session_id,
                created_at=user.created_at,
            )
            self._session.add(existing)
        await self._session.flush()
        return self._to_entity(existing)

    async def update_active_session(self, telegram_id: int, session_id: int | None) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.telegram_id == telegram_id)
            .values(active_session_id=session_id)
        )

    async def delete(self, telegram_id: int) -> None:
        await self._session.execute(
            delete(UserModel).where(UserModel.telegram_id == telegram_id)
        )

    @staticmethod
    def _to_entity(row: UserModel) -> User:
        return User(
            telegram_id=row.telegram_id,
            bot_username=row.bot_username,
            active_session_id=row.active_session_id,
            created_at=row.created_at,
        )
