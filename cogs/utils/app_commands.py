"""
Overwritten discord.app_commands

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord
from discord import app_commands

from cogs.errors import (
    UnrecognizedUrlError,
    MissingPermission,
    SubmissionAlreadyExists,
    InvalidUrlError,
    GameNotFoundError,
    SubmissionNotInDatabase,
    NoSubmissionError
)
from cogs.utils.embed import send_error_embed


__all__ = (
    "Group",
)


class Group(app_commands.Group):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        
        if isinstance(
            error,
            UnrecognizedUrlError | 
            SubmissionAlreadyExists |
            InvalidUrlError |
            GameNotFoundError |
            SubmissionNotInDatabase |
            NoSubmissionError
        ):
            assert error.message
            await send_error_embed(interaction, error.message)

        elif isinstance(error, MissingPermission):
            await send_error_embed(
                interaction=interaction,
                message=f"You can't do that since you're missing `{error.missing_permission}` permission."
            )

        else:
            raise error
