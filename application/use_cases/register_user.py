import re

from domain.entities.user import User
from domain.exceptions import UserAlreadyRegisteredError, UsernameTakenError
from domain.repositories.user_repository import UserRepository

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


class RegisterUser:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, telegram_id: int, bot_username: str) -> User:
        if not USERNAME_PATTERN.match(bot_username):
            raise ValueError(
                "Username must be 3–20 characters and contain only letters, numbers, or underscores."
            )

        existing_user = await self._user_repo.get_by_telegram_id(telegram_id)
        if existing_user:
            raise UserAlreadyRegisteredError(
                f"Telegram user {telegram_id} is already registered as '{existing_user.bot_username}'."
            )

        taken = await self._user_repo.get_by_bot_username(bot_username)
        if taken:
            raise UsernameTakenError(f"The username '{bot_username}' is already taken.")

        user = User(
            telegram_id=telegram_id,
            bot_username=bot_username.lower(),
            active_session_id=None,
        )
        return await self._user_repo.save(user)
