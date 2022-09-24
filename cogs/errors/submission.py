"""
Submission Custom Exceptions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

from discord import app_commands


__all__ = (
    "SubmissionAlreadyExists",
    "SubmissionNotInDatabase",
    "NoSubmissionError",
    "VoidGameError"
)


class SubmissionAlreadyExists(app_commands.AppCommandError):
    """An exception raised when the submission already exists."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "Submission already exists."
        super().__init__(self.message)


class SubmissionNotInDatabase(app_commands.AppCommandError):
    """An exception raised when the submission is not in the database."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "Submission not in database."
        super().__init__(self.message)


class NoSubmissionError(app_commands.AppCommandError):
    """An exception raised when there is no submission."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "No Submission."
        super().__init__(self.message)


class VoidGameError(app_commands.AppCommandError):
    """An exception raised when the game doesn't exist."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "Game doesn't exist."
        super().__init__(self.message)