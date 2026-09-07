from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError


class DatabaseError(SQLAlchemyError):
    """Base exception for database-related application errors."""

    def __init__(self, error: dict[str, str]) -> None:
        self.name = error["name"]
        self.description = error["description"]
        super().__init__(self.name)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.description}"

    def __repr__(self) -> str:
        return str(self)


class DbUrlInvalidError(SQLAlchemyError):
    def __init__(self, error: dict[str, str], message: str = ""):
        super().__init__(error)
        if not message:
            self.message = (
                "Invalid DB URL was provided. Please check the URL and try again."
            )
        else:
            self.message = message


class EmptyDatabaseError(DatabaseError):
    """Raised when a database query returns no links."""

    def __init__(self, error: dict[str, str], message: str = ""):
        super().__init__(error)
        if not message:
            self.message = "The database query returned no results."
        else:
            self.message = message


class DBEngineError(DatabaseError):
    """Raised when a database engine is unavailable."""

    def __init__(self, error: dict[str, str], message: str = ""):
        super().__init__(error)
        if not message:
            self.message = "The database engine is unavailable. Please check the database engine configuration."
        else:
            self.message = message


class DBSessionError(DBEngineError):
    """Raised when a database session operation fails."""

    def __init__(self, error: dict[str, str], message: str = ""):
        super().__init__(error)
        if not message:
            self.message = "The database session operation failed. Please check the database connection and try again."
        else:
            self.message = message
