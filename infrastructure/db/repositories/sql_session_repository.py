from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.session import ChatSession, SessionStatus
from domain.repositories.session_repository import SessionRepository
from infrastructure.db.models import SessionModel


class SqlSessionRepository(SessionRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, session_id: int) -> ChatSession | None:
        row = await self._session.get(SessionModel, session_id)
        return self._to_entity(row) if row else None

    async def get_active_session_for_user(self, telegram_id: int) -> ChatSession | None:
        result = await self._session.execute(
            select(SessionModel).where(
                or_(
                    SessionModel.requester_id == telegram_id,
                    SessionModel.receiver_id == telegram_id,
                ),
                SessionModel.status == SessionStatus.ACTIVE.value,
            )
        )
        row = result.scalars().first()
        return self._to_entity(row) if row else None

    async def get_sessions_for_user(self, telegram_id: int) -> list[ChatSession]:
        result = await self._session.execute(
            select(SessionModel).where(
                or_(
                    SessionModel.requester_id == telegram_id,
                    SessionModel.receiver_id == telegram_id,
                ),
                SessionModel.status.in_([SessionStatus.ACTIVE.value, SessionStatus.ENDED.value]),
            )
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_pending_between(self, requester_id: int, receiver_id: int) -> ChatSession | None:
        result = await self._session.execute(
            select(SessionModel).where(
                SessionModel.requester_id == requester_id,
                SessionModel.receiver_id == receiver_id,
                SessionModel.status == SessionStatus.PENDING.value,
            )
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save(self, session: ChatSession) -> ChatSession:
        if session.id == 0:
            row = SessionModel(
                requester_id=session.requester_id,
                receiver_id=session.receiver_id,
                status=session.status.value,
                created_at=session.created_at,
            )
            self._session.add(row)
            await self._session.flush()
            session.id = row.id
            return self._to_entity(row)

        row = await self._session.get(SessionModel, session.id)
        if row:
            row.status = session.status.value
            await self._session.flush()
        return session

    async def update_status(self, session_id: int, status: SessionStatus) -> None:
        await self._session.execute(
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(status=status.value)
        )

    async def delete_all_for_user(self, telegram_id: int) -> list[int]:
        active = await self.get_active_session_for_user(telegram_id)
        partner_ids = [active.other_participant(telegram_id)] if active else []

        await self._session.execute(
            delete(SessionModel).where(
                or_(
                    SessionModel.requester_id == telegram_id,
                    SessionModel.receiver_id == telegram_id,
                )
            )
        )
        return partner_ids

    @staticmethod
    def _to_entity(row: SessionModel) -> ChatSession:
        return ChatSession(
            id=row.id,
            requester_id=row.requester_id,
            receiver_id=row.receiver_id,
            status=SessionStatus(row.status),
            created_at=row.created_at,
        )
