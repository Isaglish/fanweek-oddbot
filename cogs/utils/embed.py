"""
Utility functions for embeds.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

import discord


__all__ = (
    "create_embed_with_author",
    "send_error_embed"
)


def create_embed_with_author(
    color: discord.Color,
    description: str,
    author: str | discord.Member,
    author_icon_url: Optional[str] = None
) -> discord.Embed:
    if not author_icon_url:
        if not isinstance(author, discord.Member):
            raise TypeError("Author doesn't have 'avatar' attribute.")

        author_icon_url = author.avatar.url

    embed = discord.Embed(color=color, description=description)
    embed.set_author(name=author, icon_url=author_icon_url)

    return embed


async def send_error_embed(interaction: discord.Interaction, message: str) -> None:
    embed = create_embed_with_author(
        discord.Color.red(),
        message,
        interaction.user
    )
    try:
        await interaction.response.send_message(embed=embed)
    except discord.InteractionResponded:
        await interaction.edit_original_response(embed=embed)
        