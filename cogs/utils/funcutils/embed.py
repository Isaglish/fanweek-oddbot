"""
Utility functions for embeds.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord


__all__ = (
    "create_embed_with_author",
    "send_error_embed"
)


def create_embed_with_author(
    color: discord.Color,
    description: str,
    author_name: str,
    author_icon_url: str
) -> discord.Embed:

    embed = discord.Embed(color=color, description=description)
    embed.set_author(name=author_name, icon_url=author_icon_url)

    return embed


async def send_error_embed(interaction: discord.Interaction, message: str) -> None:
    embed = create_embed_with_author(
        discord.Color.red(),
        message,
        interaction.user,
        interaction.user.avatar.url
    )
    try:
        await interaction.response.send_message(embed=embed)
    except discord.InteractionResponded:
        await interaction.edit_original_response(embed=embed)
        