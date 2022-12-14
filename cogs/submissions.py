"""
Main feature of Odd Bot, keeps track of submissions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import string
import random
from io import BytesIO
from typing import Optional, TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs import utils, errors
from cogs.utils.views import Confirm, EmbedPaginator

if TYPE_CHECKING:
    from bot import OddBot


class Submission(commands.Cog):

    __slots__ = "bot", "log", "open_source_files"

    def __init__(self, bot: "OddBot") -> None:
        self.bot = bot
        self.log = bot.log
        self.open_source_files = bot.config["open_source_files"]


    # groups
    submissions_group = utils.app_commands.Group(name="submissions", description="Commands related to submissions.")


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

        embed = utils.embed.create_embed_with_author(
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
                WHERE guild_id=$1 AND game_url=$2
                """,
                interaction.guild_id,
                game_url
            )
        game_attrs = await utils.submission.get_game_attrs(game_url)

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

        game_exists = await utils.submission.game_exists_check(game_id)
        if game_exists and game_attrs["title"] == "Fancade":  # has an image but no title
            identifier = "".join(random.choices(string.ascii_letters, k=6))
            game_attrs["title"] = f"?ULG_{identifier}?"

        elif not game_exists and game_attrs["title"] == "Fancade":  # has no image and no title
            raise errors.GameNotFoundError("Hmm.. It seems like that game doesn't exist.")

        if member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                await connection.execute(
                    "INSERT INTO submission (author_id, guild_id, game_title, game_url) VALUES ($1, $2, $3, $4)",
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
                    "INSERT INTO submission (author_id, guild_id, game_title, game_url) VALUES ($1, $2, $3, $4)",
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
                WHERE guild_id=$1 AND game_url=$2
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

            embed = utils.embed.create_embed_with_author(
                color=discord.Color.orange(),
                description=f"This will delete the submission **{result['game_title']}** which was submitted by **{author}**. Are you sure you wanna proceed?",
                author=interaction.user
            )
            await interaction.response.send_message(embed=embed, view=view)

        if author.id == interaction.user.id:
            embed = utils.embed.create_embed_with_author(
                color=discord.Color.orange(),
                description=f"This will delete your submission **{result['game_title']}**. Are you sure you wanna proceed?",
                author=interaction.user
            )
            await interaction.response.send_message(embed=embed, view=view)

        await utils.submission.handle_confirm_view(
            config=self.bot.config,
            bot=self.bot,
            interaction=interaction,
            view=view,
            exec_args=("DELETE FROM submission WHERE game_url=$1", result["game_url"]),
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
                    WHERE game_title ~* $1 AND guild_id=$2
                    ORDER BY author_id
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
                    WHERE game_title ~* $1 AND guild_id=$2 AND author_id=$3
                    ORDER BY author_id
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
                    WHERE guild_id=$1
                    ORDER BY author_id
                    """,
                    interaction.guild_id
                )
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            user = None

        elif member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id=$1 AND author_id=$2
                    ORDER BY author_id
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
                    WHERE guild_id=$1 AND author_id=$2
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

        embed = utils.embed.create_embed_with_author(
            color=discord.Color.blue(),
            description=f"{self.bot.config['loading_emoji']} Loading submissions...",
            author=interaction.user
        )
        await interaction.response.send_message(embed=embed)

        embeds = await utils.submission.create_submissions_embed(interaction, results, user, show_all)
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
                    WHERE guild_id=$1
                    ORDER BY author_id
                    """,
                    interaction.guild_id
                )
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            success_message = "All submissions have been deleted."
            confirm_message = "This will delete everyone's submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id=$1", interaction.guild_id)

            if not can_manage_guild:
                raise errors.MissingPermission("Manage Server")

        elif member is None or member == interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id=$1 AND author_id=$2
                    ORDER BY author_id
                    """,
                    interaction.guild_id,
                    interaction.user.id
                )
            no_submission_message = "You haven't submitted anything yet."
            success_message = "Deleted all of your submissions."
            confirm_message = "This will delete all of your submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id=$1 AND author_id=$2", interaction.guild_id, interaction.user.id)

        elif member is not None or member != interaction.user:
            async with self.bot.pool.acquire() as connection:
                results = await connection.fetch(
                    """SELECT * FROM submission
                    WHERE guild_id=$1 AND author_id=$2
                    ORDER BY author_id
                    """,
                    interaction.guild_id,
                    member.id
                )
            no_submission_message = f"**{member}** hasn't submitted anything yet."
            success_message = f"Deleted all of **{member}**'s submissions."
            confirm_message = f"This will delete all of **{member}**'s submissions. Are you sure you wanna proceed?"
            exec_args = ("DELETE FROM submission WHERE guild_id=$1 AND author_id=$2", interaction.guild_id, member.id)

            if not can_manage_guild:
                raise errors.MissingPermission("Manage Server")

        if not results:
            raise errors.NoSubmissionError(no_submission_message)

        view = Confirm(interaction.user)

        embed = utils.embed.create_embed_with_author(
            color=discord.Color.orange(),
            description=confirm_message,
            author=interaction.user
        )
        await interaction.response.send_message(embed=embed, view=view)

        await utils.submission.handle_confirm_view(
            config=self.bot.config,
            bot=self.bot,
            interaction=interaction,
            view=view,
            exec_args=exec_args,
            results=results,
            success_message=success_message,
            delete_many=True
        )


    @app_commands.command(name="getsource", description="Gets the source of the file and sends it to you.")
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
            await utils.embed.send_error_embed(interaction, error.message)
        else:
            raise error


async def setup(bot: "OddBot") -> None:
    await bot.add_cog(Submission(bot))
