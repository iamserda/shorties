from __future__ import annotations


class DatabaseError(Exception):
    """Custom exception for database errors."""

    def __init__(self, error: dict) -> None:
        super().__init__(error["name"])
        self.description = error["description"]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.description}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.description}"


class EmptyDatabaseError(DatabaseError):
    """Custom exception for empty database errors."""


class DBEngineError(DatabaseError):
    """Custom exception for database engine errors."""
