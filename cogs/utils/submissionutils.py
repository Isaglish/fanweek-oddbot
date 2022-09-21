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
    "send_error_message",
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


async def send_error_message(interaction: discord.Interaction, message: str) -> None:
    embed = discord.Embed(color=discord.Color.red(), description=message)
    embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
    try:
        await interaction.response.send_message(embed=embed)
    except discord.InteractionResponded:
        await interaction.edit_original_response(embed=embed)


async def create_submissions_embed(
    interaction: discord.Interaction,
    query: list[dict[str, Any]],
    member: Optional[discord.Member] = None,
    show_all: bool = True
) -> list[discord.Embed]:
    embeds = []
    k = 10
    for i in range(0, len(query), 10):
        current = query[i:k]
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
            embed = discord.Embed(color=discord.Color.blue(), description=f"**Showing all submissions:**\n\n{info}")
            embed.set_author(name=f"{interaction.guild} Submissions", icon_url=interaction.guild.icon.url)
        else:
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"**Showing all of {member}'s submissions:**\n\n{info}"
            )
            embed.set_author(name=f"{interaction.user}", icon_url=interaction.user.avatar.url)

        embeds.append(embed)

    return embeds


async def handle_unsubmit_confirm_view(
    _self: commands.Cog,
    interaction: discord.Interaction,
    view: discord.ui.View,
    post: dict[str, Any],
    query: dict[str, Any]
) -> None:

    await view.wait()
    if view.value is None:
        embed = discord.Embed(color=discord.Color.red(), description="You took too long to respond.")
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
        await interaction.edit_original_response(embed=embed)

    elif view.value:
        embed = discord.Embed(color=discord.Color.blue(), description=f"{_self.bot.config['loading_emoji']} Deleting submission...")
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
        await interaction.edit_original_response(embed=embed, view=None)

        _self.db.delete_one(post)

        embed.description = f"The game **{query['title']}** has been removed from the database."
        embed.color = discord.Color.green()
        await interaction.edit_original_response(embed=embed, view=None)

    else:
        embed = discord.Embed(color=discord.Color.red(), description="Command has been cancelled.")
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
        await interaction.edit_original_response(embed=embed, view=None)