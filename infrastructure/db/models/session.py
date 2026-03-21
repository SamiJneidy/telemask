from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.entities.session import SessionStatus
from infrastructure.db.models.base import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(SessionStatus, values_callable=lambda e: [v.value for v in e]),
        nullable=False,
        default=SessionStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    requester: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[requester_id], back_populates="sessions_as_requester"
    )
    receiver: Mapped["UserModel"] = relationship(
        "UserModel", foreign_keys=[receiver_id], back_populates="sessions_as_receiver"
    )
