"""
URL Custom Exceptions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

from cogs.errors import CustomMessageError


__all__ = (
    "UnrecognizedUrlError",
    "InvalidUrlError"
)


class UnrecognizedUrlError(CustomMessageError):
    """An exception raised when the provided url is not recognized as Fancade."""
    
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Unrecognized URL provided.")


class InvalidUrlError(CustomMessageError):
    """An exception raised when the provided url is not a valid Fancade URL."""

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Invalid URL provided.")
        