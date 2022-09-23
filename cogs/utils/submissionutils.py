"""
Utility functions for submissions.py

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional, Any

import discord
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands


__all__ = (
    "get_game_attrs",
    "check_game_exists",
    "create_embed_with_author",
    "send_error_embed",
    "create_submissions_embed",
    "handle_unsubmit_confirm_view"
)


async def get_game_attrs(link: str) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            r = await response.text()
            doc = BeautifulSoup(r, "html.parser")
            title = doc.find("title").text
            author = doc.find("p", class_="author").text
            image_url = doc.find("meta", attrs={"property": "og:image"}).attrs["content"]
            description = doc.find("meta", attrs={"name": "description"}).attrs["content"]

    return {"title": title, "image_url": image_url, "description": description, "author": author}


async def check_game_exists(id: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.fancade.com/images/{id}.jpg") as response:
            try:
                r = await response.text()
                doc = BeautifulSoup(r, "html.parser")
                page_not_found = doc.find("h1").text

                if page_not_found == "Page Not Found":
                    return False

            except UnicodeDecodeError:
                return True


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


async def create_submissions_embed(
    interaction: discord.Interaction,
    documents: list[dict[str, Any]],
    member: Optional[discord.Member] = None,
    show_all: bool = True
) -> list[discord.Embed]:
    embeds = []
    k = 10
    for i in range(0, len(documents), 10):
        current = documents[i:k]
        k += 10

        number = i
        infos = []
        for submission in current:
            number += 1
            user = await interaction.guild.fetch_member(submission["author_id"])

            if show_all:
                infos.append(f"**{number}.** [{submission['title']}]({submission['link']}) • {user}")
            else:
                infos.append(f"**{number}.** [{submission['title']}]({submission['link']})")

        info = "\n".join(infos)

        if show_all:
            embed = create_embed_with_author(
                discord.Color.blue(),
                f"**Showing all submissions:**\n\n{info}",
                f"{interaction.guild} Submissions",
                interaction.guild.icon.url
            )
        else:
            embed = create_embed_with_author(
                discord.Color.blue(),
                f"**Showing all of {member}'s submissions:**\n\n{info}",
                interaction.user,
                interaction.guild.icon.url
            )

        embeds.append(embed)

    return embeds


async def handle_confirm_view(
    _self: commands.Cog,
    interaction: discord.Interaction,
    view: discord.ui.View,
    post: dict[str, Any],
    documents: dict[str, Any] | list[dict[str, Any]],
    success_message: str = None,
    delete_many: bool = False
) -> None:

    if not delete_many:
        confirm_message = f"{_self.bot.config['loading_emoji']} Deleting submission..."
        success_message = f"The game **{documents['title']}** has been removed from the database."
    else:
        confirm_message = f"{_self.bot.config['loading_emoji']} Deleting submissions..."
        success_message = success_message

    await view.wait()
    if view.value is None:
        embed = create_embed_with_author(
            discord.Color.red(),
            "You took too long to respond.",
            interaction.user,
            interaction.user.avatar.url
        )
        await interaction.edit_original_response(embed=embed)

    elif view.value:
        embed = create_embed_with_author(
            discord.Color.blue(),
            confirm_message,
            interaction.user,
            interaction.user.avatar.url
        )
        await interaction.edit_original_response(embed=embed, view=None)

        if not delete_many:
            await _self.db.delete_one(post)
        else:
            await _self.db.delete_many(post)
            embed.set_footer(text=f"Deleted a total of {len(documents)} submissions.")

        embed.description = success_message
        embed.color = discord.Color.green()
        await interaction.edit_original_response(embed=embed, view=None)

    else:
        embed = create_embed_with_author(
            discord.Color.red(),
            "Command has been cancelled.",
            interaction.user,
            interaction.user.avatar.url
        )
        await interaction.edit_original_response(embed=embed, view=None)
