from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    telegram_id: int
    bot_username: str
    active_session_id: int | None
    created_at: datetime = field(default_factory=datetime.utcnow)
