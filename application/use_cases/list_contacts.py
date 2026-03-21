from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class ListContacts:
    """Return the unique set of users this person has ever chatted with."""

    def __init__(self, session_repo: SessionRepository, user_repo: UserRepository) -> None:
        self._session_repo = session_repo
        self._user_repo = user_repo

    async def execute(self, telegram_id: int) -> list[tuple[int, str]]:
        """
        Returns a list of (other_telegram_id, other_bot_username) tuples.
        Each contact appears once regardless of how many sessions they share.
        Ordered by most recent session first.
        """
        sessions = await self._session_repo.get_sessions_for_user(telegram_id)
        sessions_sorted = sorted(sessions, key=lambda s: s.created_at, reverse=True)

        seen: set[int] = set()
        result: list[tuple[int, str]] = []

        for session in sessions_sorted:
            other_id = session.other_participant(telegram_id)
            if other_id in seen:
                continue
            seen.add(other_id)
            other_user = await self._user_repo.get_by_telegram_id(other_id)
            username = other_user.bot_username if other_user else "unknown"
            result.append((other_id, username))

        return result
