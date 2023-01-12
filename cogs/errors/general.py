"""
General Custom Exceptions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

from discord import app_commands


__all__ = (
    "CustomMessageError",
    "MissingPermission",
    "FileForbiddenAccess"
)


class CustomMessageError(app_commands.AppCommandError):
    """Base class for custom errors that have the message attribute."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message
        super().__init__(self.message)


class FileForbiddenAccess(CustomMessageError):
    """An exception raised when you don't have access to the file."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "You don't have access to that file.")


class MissingPermission(app_commands.AppCommandError):
    """An exception raised when the member is missing a permission."""

    def __init__(self, missing_permission: str) -> None:
        self.missing_permission = missing_permission
        super().__init__(f"Member missing {missing_permission} permission.")
