"""
Main feature of Odd Bot, keeps track of submissions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import string
import random
from io import BytesIO
from typing import Optional, TYPE_CHECKING, Any

import aiohttp
import asyncpg
import discord
from discord import app_commands
from discord.ext import commands
from bs4 import BeautifulSoup, Tag

from cogs import errors
from cogs.utils.view import Confirm
from cogs.utils.embed import EmbedPaginator, create_embed_with_author, send_error_embed
from cogs.utils.app_commands import Group

if TYPE_CHECKING:
    from bot import OddBot


async def handle_confirm_view(
    config: dict[str, Any],
    bot: "OddBot",
    interaction: discord.Interaction,
    view: Confirm,
    exec_args: tuple[Any, ...],
    results: asyncpg.Record | list[asyncpg.Record],
    success_message: Optional[str] = None,
    delete_many: bool = False
) -> None:

    confirm_message = f"{config['loading_emoji']} Deleting submission{'s' if delete_many else ''}..."

    if isinstance(results, asyncpg.Record):
        success_message = f"The game **{results['game_title']}** has been removed from the database."

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

        query, *args = exec_args

        if not delete_many:
            async with bot.pool.acquire() as connection:
                await connection.execute(query, *args)
        else:
            async with bot.pool.acquire() as connection:
                await connection.execute(query, *args)
            embed.set_footer(text=f"Deleted a total of {len(results)} submissions.")

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


async def create_submissions_embed(
    interaction: discord.Interaction,
    results: list[asyncpg.Record],
    member: Optional[discord.Member | discord.User] = None,
    show_all: bool = True
) -> list[discord.Embed]:

    assert interaction.guild
    assert interaction.guild.icon

    embeds = []

    end = 10
    for start in range(0, len(results), 10):
        current_submissions = results[start:end]
        end += 10
        
        items = []
        for item_index, submission in enumerate(current_submissions, start=start+1):
            user = interaction.guild.get_member(submission["author_id"])
            items.append(f"**{item_index}.** [{submission['game_title']}]({submission['game_url']}){f' • {user}' if show_all else ''}")

        item = "\n".join(items)

        embed = create_embed_with_author(
            color=discord.Color.blue(),
            description=f"**Showing all submissions:**\n\n{item}" if show_all else f"**Showing all of {member}'s submissions:**\n\n{item}",
            author=f"{interaction.guild} Submissions (Total: {len(results)})" if show_all else interaction.user,
            icon_url=interaction.guild.icon.url if show_all else None
        )
        embeds.append(embed)

    return embeds


async def game_exists_check(game_id: str) -> bool:
    async with aiohttp.ClientSession() as session, session.get(f"https://www.fancade.com/images/{game_id}.jpg") as response:
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


async def get_game_attrs(game_url: str) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session, session.get(game_url) as response:
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


class Submission(commands.Cog):

    __slots__ = "bot", "log", "open_source_files"

    def __init__(self, bot: "OddBot") -> None:
        self.bot = bot
        self.log = bot.log
        self.open_source_files = bot.config["open_source_files"]

    # groups
    submissions_group = Group(name="submissions", description="Commands related to submissions.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.log.info(f"{self.__class__.__name__.lower()} module is ready.")

    @submissions_group.command(name="submit", description="Submits your game to the database")
    @app_commands.describe(
        game_url="Your game's url, you can get this by sharing your game in Fancade.",
        member="The member you want to submit for. This requires Manage Server permission."
    )
    async def submit_command(
        self,
        interaction: discord.Interaction,
        game_url: str,
        member: Optional[discord.Member] = None
    ) -> None:

        assert isinstance(interaction.user, discord.Member)
        assert interaction.guild

        embed = create_embed_with_author(
            color=discord.Color.blue(),
            description=f"{self.bot.config['loading_emoji']} Processing submission...",
            author=interaction.user
        )
        await interaction.response.send_message(embed=embed)

        if not game_url.startswith("https://play.fancade.com/"):
            raise errors.UnrecognizedUrlError("I don't recognize that URL.")

        async with self.bot.pool.acquire() as connection:
            result = await connection.fetchrow(
                """
                SELECT author_id, game_title FROM submission
                WHERE guild_id = $1 AND game_url = $2;
                """,
                interaction.guild_id,
                game_url
            )
        game_attrs = await get_game_attrs(game_url)

        can_manage_guild = interaction.user.guild_permissions.manage_guild
        if not can_manage_guild and member != interaction.user and member is not None:
            raise errors.MissingPermission("Manage Server")

        if result is not None:
            author = interaction.guild.get_member(result["author_id"])
            raise errors.SubmissionAlreadyExists(
                f"The game **{result['game_title']}** has already been submitted by **{author}**."
            )

        game_id = game_url[25:]
        if len(game_id) != 16:
            raise errors.InvalidUrlError("That is an invalid URL.")

        game_exists = await game_exists_check(game_id)
        if game_exists and game_attrs["title"] == "Fancade":  # has an image but no title
            identifier = "".join(random.choices(string.ascii_letters, k=6))
            game_attrs["title"] = f"?ULG_{identifier}?"

        elif not game_exists and game_attrs["title"] == "Fancade":  # has no image and no title
            raise errors.GameNotFoundError("Hmm.. It seems like that game doesn't exist.")

        if member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO submission (author_id, guild_id, game_title, game_url) VALUES ($1, $2, $3, $4);",
                    interaction.user.id,
                    interaction.guild_id,
                    game_attrs["title"],
                    game_url
                )

            embed.description = f"{interaction.user.mention}, your game **{game_attrs['title']}** was submitted successfully."
            embed.set_thumbnail(url=game_attrs["image_url"])

        else:
            assert member.avatar
            async with self.bot.pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO submission (author_id, guild_id, game_title, game_url) VALUES ($1, $2, $3, $4);",
                    member.id,
                    interaction.guild_id,
                    game_attrs["title"],
                    game_url
                )

            embed.description = f"{interaction.user.mention}, the game **{game_attrs['title']}** was submitted successfully."
            embed.set_thumbnail(url=game_attrs["image_url"])
            embed.set_footer(text=f"Submitted for {member}", icon_url=member.avatar.url)

        await interaction.edit_original_response(embed=embed)

    @submissions_group.command(name="unsubmit", description="Unsubmits your game from the database")
    @app_commands.describe(game_url="Your game's URL, you can get this by sharing your game in Fancade.")
    async def unsubmit_command(self, interaction: discord.Interaction, game_url: str) -> None:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.guild

        if not game_url.startswith("https://play.fancade.com/"):
            raise errors.UnrecognizedUrlError("I don't recognize that URL.")

        async with self.bot.pool.acquire() as connection:
            result = await connection.fetchrow(
                """
                SELECT author_id, game_title, game_url FROM submission
                WHERE guild_id = $1 AND game_url = $2;
                """,
                interaction.guild_id,
                game_url
            )

        if result is None:
            raise errors.SubmissionNotInDatabase("I can't find that game in the database.")

        author = interaction.guild.get_member(result["author_id"])
        assert author
        view = Confirm(interaction.user)

        can_manage_guild = interaction.user.guild_permissions.manage_guild
        if author.id != interaction.user.id:
            if not can_manage_guild:
                raise errors.MissingPermission("Manage Server")

            embed = create_embed_with_author(
                color=discord.Color.orange(),
                description=f"This will delete the submission **{result['game_title']}** which was submitted by **{author}**. Are you sure you wanna proceed?",
                author=interaction.user
            )
            await interaction.response.send_message(embed=embed, view=view)

        if author.id == interaction.user.id:
            embed = create_embed_with_author(
                color=discord.Color.orange(),
                description=f"This will delete your submission **{result['game_title']}**. Are you sure you wanna proceed?",
                author=interaction.user
            )
            await interaction.response.send_message(embed=embed, view=view)

        await handle_confirm_view(
            config=self.bot.config,
            bot=self.bot,
            interaction=interaction,
            view=view,
            exec_args=("DELETE FROM submission WHERE game_url = $1;", result["game_url"]),
            results=result
        )

    @unsubmit_command.autocomplete("game_url")
    async def unsubmit_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.guild

        if interaction.user.guild_permissions.manage_guild:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """
                    SELECT * FROM submission
                    WHERE game_title ~* $1 AND guild_id = $2
                    ORDER BY author_id;
                    """,
                    current,
                    interaction.guild_id
                )
            return [
                app_commands.Choice(
                    name=f"{result['game_title']} by {interaction.guild.get_member(result['author_id'])}",
                    value=result["game_url"]
                ) for result in results
            ]
        else:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """
                    SELECT * FROM submission
                    WHERE game_title ~* $1 AND guild_id = $2 AND author_id = $3
                    ORDER BY author_id;
                    """,
                    current,
                    interaction.guild_id,
                    interaction.user.id
                )
            return [
                app_commands.Choice(name=result['game_title'], value=result["game_url"]) for result in results
            ]

    @submissions_group.command(name="show", description="Shows your (or another person's) submissions.")
    @app_commands.describe(
        member="The member you want to show the submissions of.",
        show_all="This will show everyone's submissions."
    )
    @app_commands.rename(show_all="all")
    async def show_submissions_command(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        show_all: bool = False
    ) -> None:
        
        assert interaction.guild

        if show_all:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1
                    ORDER BY author_id;
                    """,
                    interaction.guild_id
                )
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            user = None

        elif member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1 AND author_id = $2
                    ORDER BY author_id;
                    """,
                    interaction.guild_id,
                    interaction.user.id
                )
            no_submission_message = "You haven't submitted anything yet."
            show_all = False
            user = interaction.user

        elif member is not None or member != interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1 AND author_id = $2
                    ORDER BY author_id
                    """,
                    interaction.guild_id,
                    member.id
                )
            no_submission_message = f"**{member}** hasn't submitted anything yet."
            show_all = False
            user = member

        if not results:
            raise errors.NoSubmissionError(no_submission_message)

        embed = create_embed_with_author(
            color=discord.Color.blue(),
            description=f"{self.bot.config['loading_emoji']} Loading submissions...",
            author=interaction.user
        )
        await interaction.response.send_message(embed=embed)

        embeds = await create_submissions_embed(interaction, results, user, show_all)
        paginator = EmbedPaginator(interaction, embeds)
        
        embed = paginator.index_page
        await interaction.edit_original_response(embed=embed, view=paginator)       

    @submissions_group.command(name="clear", description="Clears your (or another person's) submissions.")
    @app_commands.describe(
        member="The member you want to clear the submissions of. This requires Manage Server permission.",
        clear_all="This will clear everyone's submissions. This requires Manage Server permission."
    )
    @app_commands.rename(clear_all="all")
    async def clear_submissions_command(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        clear_all: bool = False
    ) -> None:

        assert isinstance(interaction.user, discord.Member)
        assert interaction.guild

        can_manage_guild = interaction.user.guild_permissions.manage_guild

        if clear_all:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1
                    ORDER BY author_id;
                    """,
                    interaction.guild_id
                )
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            success_message = "All submissions have been deleted."
            confirm_message = "This will delete everyone's submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id = $1", interaction.guild_id)

            if not can_manage_guild:
                raise errors.MissingPermission("Manage Server")

        elif member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1 AND author_id = $2
                    ORDER BY author_id;
                    """,
                    interaction.guild_id,
                    interaction.user.id
                )
            no_submission_message = "You haven't submitted anything yet."
            success_message = "Deleted all of your submissions."
            confirm_message = "This will delete all of your submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id = $1 AND author_id = $2", interaction.guild_id, interaction.user.id)

        elif member is not None or member != interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id = $1 AND author_id = $2
                    ORDER BY author_id;
                    """,
                    interaction.guild_id,
                    member.id
                )
            no_submission_message = f"**{member}** hasn't submitted anything yet."
            success_message = f"Deleted all of **{member}**'s submissions."
            confirm_message = f"This will delete all of **{member}**'s submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id = $1 AND author_id = $2", interaction.guild_id, member.id)

            if not can_manage_guild:
                raise errors.MissingPermission("Manage Server")

        if not results:
            raise errors.NoSubmissionError(no_submission_message)

        view = Confirm(interaction.user)

        embed = create_embed_with_author(
            color=discord.Color.orange(),
            description=confirm_message,
            author=interaction.user
        )
        await interaction.response.send_message(embed=embed, view=view)

        await handle_confirm_view(
            config=self.bot.config,
            bot=self.bot,
            interaction=interaction,
            view=view,
            exec_args=exec_args,
            results=results,
            success_message=success_message,
            delete_many=True
        )

    @app_commands.command(name="get-source", description="Gets the source of the file and sends it to you.")
    @app_commands.describe(file_name="The name of the file you want to get the source of.")
    async def get_source(self, interaction: discord.Interaction, file_name: str) -> None:
        if file_name not in self.open_source_files:
            raise errors.FileForbiddenAccess("Sorry, but you either can't access that file or it doesn't exist.")

        with open(file_name, "r") as f:
            buffer = BytesIO(f.read().encode("utf8"))

        file = discord.File(buffer, file_name)
        await interaction.response.send_message(file=file)

    @get_source.autocomplete("file_name")
    async def get_source_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=source_name, value=source_name) for source_name in self.open_source_files
        ]

    @get_source.error
    async def on_get_source_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:

        if isinstance(error, errors.FileForbiddenAccess):
            assert error.message
            await send_error_embed(interaction, error.message)
        else:
            raise error
            

async def setup(bot: "OddBot") -> None:
    await bot.add_cog(Submission(bot))
