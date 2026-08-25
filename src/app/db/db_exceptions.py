from __future__ import annotations


class DatabaseError(Exception):
    """Base exception for database-related application errors."""

    def __init__(self, error: dict[str, str]) -> None:
        self.name = error["name"]
        self.description = error["description"]
        super().__init__(self.name)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.description}"

    def __repr__(self) -> str:
        return str(self)


class EmptyDatabaseError(DatabaseError):
    """Raised when a database query returns no links."""


class DBEngineError(DatabaseError):
    """Raised when a database engine is unavailable."""


class DBSessionError(DBEngineError):
    """Raised when a database session operation fails."""
