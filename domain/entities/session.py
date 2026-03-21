from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    DECLINED = "declined"


@dataclass
class ChatSession:
    id: int
    requester_id: int
    receiver_id: int
    status: SessionStatus
    created_at: datetime = field(default_factory=datetime.utcnow)

    def other_participant(self, user_telegram_id: int) -> int:
        """Return the telegram_id of the other person in this session."""
        if user_telegram_id == self.requester_id:
            return self.receiver_id
        return self.requester_id
