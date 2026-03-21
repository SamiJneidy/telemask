class UsernameTakenError(Exception):
    """Raised when a chosen bot_username is already registered."""


class UserNotFoundError(Exception):
    """Raised when a user lookup returns no result."""


class UserAlreadyRegisteredError(Exception):
    """Raised when a telegram_id tries to register twice."""


class SessionNotFoundError(Exception):
    """Raised when a chat session cannot be found."""


class CannotChatWithYourselfError(Exception):
    """Raised when a user tries to open a chat with their own username."""


class PendingRequestAlreadyExistsError(Exception):
    """Raised when a pending request between two users already exists."""


class NoActiveSessionError(Exception):
    """Raised when an action requires an active session but none is set."""


class NotAParticipantError(Exception):
    """Raised when a user tries to act on a session they are not part of."""
