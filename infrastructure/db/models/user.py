from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.db.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bot_username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    active_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions_as_requester: Mapped[list["SessionModel"]] = relationship(
        "SessionModel",
        foreign_keys="SessionModel.requester_id",
        back_populates="requester",
        lazy="select",
    )
    sessions_as_receiver: Mapped[list["SessionModel"]] = relationship(
        "SessionModel",
        foreign_keys="SessionModel.receiver_id",
        back_populates="receiver",
        lazy="select",
    )
