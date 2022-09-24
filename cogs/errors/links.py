"""
Links Custom Exceptions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

from discord import app_commands


__all__ = (
    "UnrecognizedLinkError",
    "InvalidLinkError"
)


class UnrecognizedLinkError(app_commands.AppCommandError):
    """An exception raised when the provided url is not recognized as Fancade."""
    
    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "Unrecognized link provided. "
        super().__init__(self.message)


class InvalidLinkError(app_commands.AppCommandError):
    """An exception raised when the provided url is not a valid Fancade link."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or "Invalid link provided."
        super().__init__(self.message)