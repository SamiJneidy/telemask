from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from infrastructure.db.models import Base

_engine = None
_session_factory = None


def init_db(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session_factory() -> async_sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _session_factory
