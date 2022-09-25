"""
Utility functions for submissions.py

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional, Any

import discord
import aiohttp
from bs4 import BeautifulSoup, Tag

from cogs.utils.views import Confirm
from cogs.utils.database import Database
from cogs.utils.embed import create_embed_with_author


__all__ = (
    "get_game_attrs",
    "check_game_exists",
    "create_submissions_embed",
    "handle_confirm_view"
)


async def get_game_attrs(link: str) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session, session.get(link) as response:
        r = await response.text()
        doc = BeautifulSoup(r, "html.parser")

        title = doc.find("title")
        title = getattr(title, "text", title)

        author = doc.find("p", class_="author")

        image_url = doc.find("meta", attrs={"property": "og:image"})
        description = doc.find("meta", attrs={"name": "description"})

        assert isinstance(image_url, Tag)
        assert isinstance(description, Tag)

        image_url = image_url.attrs["content"]
        description = description.attrs["content"]

    return {"title": title, "image_url": image_url, "description": description, "author": author}


async def check_game_exists(identifier: str) -> bool:
    async with aiohttp.ClientSession() as session, session.get(f"https://www.fancade.com/images/{identifier}.jpg") as response:
        try:
            r = await response.text()
            doc = BeautifulSoup(r, "html.parser")
            page_not_found = doc.find("h1")
            page_not_found = getattr(page_not_found, "text", page_not_found)

            if page_not_found == "Page Not Found":
                return False

        except UnicodeDecodeError:
            return True

    return False


async def create_submissions_embed(
    interaction: discord.Interaction,
    documents: list[dict[str, Any]],
    member: Optional[discord.Member | discord.User] = None,
    show_all: bool = True
) -> list[discord.Embed]:

    assert interaction.guild
    assert interaction.guild.icon

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

            infos.append(f"**{number}.** [{submission['title']}]({submission['link']}){f' • {user}' if show_all else ''}")

        info = "\n".join(infos)

        embed = create_embed_with_author(
            color=discord.Color.blue(),
            description=f"**Showing all submissions:**\n\n{info}" if show_all else f"**Showing all of {member}'s submissions:**\n\n{info}",
            author=f"{interaction.guild} Submissions" if show_all else interaction.user,
            author_icon_url=interaction.guild.icon.url
        )
        embeds.append(embed)

    return embeds


async def handle_confirm_view(
    config: dict[str, Any],
    db: Database,
    interaction: discord.Interaction,
    view: Confirm,
    post: dict[str, Any],
    documents: dict[str, Any] | list[dict[str, Any]],
    success_message: Optional[str] = None,
    delete_many: bool = False
) -> None:

    confirm_message = f"{config['loading_emoji']} Deleting submission{'s' if delete_many else ''}..."

    if isinstance(documents, dict):
        success_message = f"The game **{documents['title']}** has been removed from the database."

    await view.wait()
    if view.value is None:
        embed = create_embed_with_author(
            color=discord.Color.red(),
            description="You took too long to respond.",
            author=interaction.user
        )
        await interaction.edit_original_response(embed=embed)

    elif view.value:
        embed = create_embed_with_author(
            color=discord.Color.blue(),
            description=confirm_message,
            author=interaction.user
        )
        await interaction.edit_original_response(embed=embed, view=None)

        if not delete_many:
            await db.delete_one(post)
        else:
            await db.delete_many(post)
            embed.set_footer(text=f"Deleted a total of {len(documents)} submissions.")

        embed.description = success_message
        embed.color = discord.Color.green()
        await interaction.edit_original_response(embed=embed, view=None)

    else:
        embed = create_embed_with_author(
            color=discord.Color.red(),
            description="Command has been cancelled.",
            author=interaction.user
        )
        await interaction.edit_original_response(embed=embed, view=None)
