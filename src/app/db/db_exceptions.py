from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError


class DatabaseError(SQLAlchemyError):
    """Base exception for database-related application errors."""

    sqlexc = SQLAlchemyError()

    def __init__(self, error: dict[str, str]) -> None:
        super().__init__(error)
        self.error_name = error["name"]
        self.error_description = error["description"]

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}: {self.error_name} - {self.error_description}"
        )

    def __repr__(self) -> str:
        return str(self)


class DbUrlInvalidError(DatabaseError):
    """Raised when an invalid database URL is provided.

    Args:
        error: Details about the database error.
        message: Optional custom error message.
    """

    db_url_invalid_error: dict[str, str] = {
        "name": "db-url-invalid-error",
        "description": "The database URL is invalid or was not provided.",
    }

    def __init__(
        self,
        error: dict[str, str] = db_url_invalid_error,
        message: str = "Invalid DB URL was provided. Please check the URL and try again.",
    ):
        super().__init__(error)
        self.message = message


class EmptyDatabaseError(DatabaseError):
    """Raised when a database query returns no links.

    Args:
        error: Details about the database error.
        message: Optional custom error message.
    """

    empty_database_error: dict[str, str] = {
        "name": "empty-database-error",
        "description": "The database currently contains no links.",
    }

    def __init__(
        self,
        error: dict[str, str] = empty_database_error,
        message: str = "The database is empty. No results can be returned.",
    ):
        super().__init__(error)
        self.message = message


class DBEngineError(DatabaseError):
    """Raised when the database engine is unavailable or misconfigured.

    Args:
        error: Details about the database error, including its name and
            description.
        message: Optional custom message describing the engine failure.
    """

    db_engine_error: dict[str, str] = {
        "name": "db-engine-error",
        "description": "An error occurred with the database engine.",
    }

    def __init__(
        self,
        error: dict[str, str] = db_engine_error,
        message: str = "The database engine is unavailable. Please check the database engine configuration.",
    ):
        super().__init__(error)
        self.message = message


class DBSessionError(DBEngineError):
    """Raised when a database session operation fails.

    Args:
        error: Details about the database error, including its name and
            description.
        message: Optional custom message describing the session failure.
    """

    db_session_error: dict[str, str] = {
        "name": "db-session-error",
        "description": "A database session operation failed.",
    }

    def __init__(
        self,
        error: dict[str, str] = db_session_error,
        message: str = "The database session operation failed. Please check the database connection and try again.",
    ):
        super().__init__(error)
        self.message = message
