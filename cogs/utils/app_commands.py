"""
Overwritten discord.app_commands

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord
from discord import app_commands

from ..errors import (
    UnrecognizedLinkError,
    MissingPermission,
    SubmissionAlreadyExists,
    InvalidLinkError,
    VoidGameError,
    SubmissionNotInDatabase,
    NoSubmissionError
)
from .embed import send_error_embed


__all__ = (
    "Group",
)


class Group(app_commands.Group):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        
        if isinstance(
            error,
            UnrecognizedLinkError | 
            SubmissionAlreadyExists |
            InvalidLinkError |
            VoidGameError |
            SubmissionNotInDatabase |
            NoSubmissionError
        ):
            await send_error_embed(interaction, error.message)

        elif isinstance(error, MissingPermission):
            await send_error_embed(
                interaction,
                f"You can't do that since you're missing `{error.missing_permission}` permission."
            )

        else:
            raise error
