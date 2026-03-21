from domain.exceptions import UserNotFoundError
from domain.repositories.session_repository import SessionRepository
from domain.repositories.user_repository import UserRepository


class DeleteUser:
    """
    Permanently delete a user account.
    Ends all active sessions, removes all session records, then removes the user.
    Returns the telegram_ids of chat partners who were in an active session
    (so the caller can notify them).
    """

    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, telegram_id: int) -> list[int]:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundError("Account not found.")

        # Collect active-session partners, then wipe all sessions
        notifiable_ids = await self._session_repo.delete_all_for_user(telegram_id)

        # Delete the user record
        await self._user_repo.delete(telegram_id)

        return notifiable_ids
