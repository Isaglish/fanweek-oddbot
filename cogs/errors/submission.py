"""
Submission Custom Exceptions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

from cogs.errors import CustomMessageError

__all__ = (
    "SubmissionAlreadyExists",
    "SubmissionNotInDatabase",
    "NoSubmissionError",
    "GameNotFoundError"
)


class SubmissionAlreadyExists(CustomMessageError):
    """An exception raised when the submission already exists."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Submission already exists.")


class SubmissionNotInDatabase(CustomMessageError):
    """An exception raised when the submission is not in the database."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Submission not in database.")


class NoSubmissionError(CustomMessageError):
    """An exception raised when there is no submission."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "No Submission.")


class GameNotFoundError(CustomMessageError):
    """An exception raised when the game doesn't exist."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Game doesn't exist.")
        