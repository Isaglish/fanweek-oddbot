"""
Exceptions for submission.py

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional, Any

import discord
from discord import app_commands


__all__ = (
    "add_error_handler",
    "UnrecognizedLinkError"
)


def add_error_handler(app_cmd_group: app_commands.Group):

    for cmd in app_cmd_group.walk_commands():
        @cmd.error
        async def on_cmd_error(_self: Any, interaction: discord.Interaction, error: app_commands.AppCommandError):
            await interaction.response.send_message("hello")


class UnrecognizedLinkError(app_commands.AppCommandError):
    """An exception raised when the provided url is not recognized as Fancade."""
    
    def __init__(self, message: Optional[str] = None):
        super().__init__(message or "Sorry, but I don't recognize that link.")
