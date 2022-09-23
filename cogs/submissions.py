"""
Main feature of Odd Bot, keeps track of submissions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import string
import random
from typing import Optional
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from .utils.database import Database
from .utils.views import Confirm, EmbedPaginator
from .utils import submissionutils


class Submission(commands.Cog):

    __slots__ = "bot", "log", "db"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.log = bot.log
        self.db = Database(bot.config, "fanweek", "submissions")
        self.open_source_files = bot.config["open_source_files"]


    # groups
    submissions_group = app_commands.Group(name="submissions", description="Commands related to submissions.")


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.log.info(f"{self.__class__.__name__.lower()} module is ready.")


    @submissions_group.command(name="submit", description="Submits your game to the database")
    @app_commands.describe(
        link="Your game's link, you can get this by sharing your game in Fancade.",
        member="The member you want to submit for. This requires Manage Server permission."
    )
    async def submit_command(
        self,
        interaction: discord.Interaction,
        link: str,
        member: Optional[discord.Member] = None
    ) -> None:

        if not link.startswith("https://play.fancade.com/"):
            await submissionutils.send_error_embed(interaction, "Sorry, but I don't recognize that link.")
            return None

        can_manage_guild = interaction.user.guild_permissions.manage_guild
        document =  await self.db.find_one({"guild_id": interaction.guild_id, "link": link})
        game_attrs = await submissionutils.get_game_attrs(link)

        if not can_manage_guild and member != interaction.user and member is not None:
            await submissionutils.send_error_embed(
                interaction,
                "Sorry, you can't submit for another member since you're missing `Manage Server` permission."
            )
            return None

        if document is not None:
            author = await interaction.guild.fetch_member(document["author_id"])
            await submissionutils.send_error_embed(
                interaction,
                f"Sorry, but the game **{document['title']}** has already been submitted by **{author}**."
            )
            return None

        game_identifier_len = 16
        game_identifier = link[25:]
        if len(game_identifier) > game_identifier_len or len(game_identifier) < game_identifier_len:
            await submissionutils.send_error_embed(interaction, "Sorry, but I can't find that game.")
            return None

        game_exists = await submissionutils.check_game_exists(game_identifier)
        if game_exists and game_attrs["title"] == "Fancade":  # has an image but no title
            identifier = "".join(random.choices(string.ascii_letters, k=6))
            game_attrs["title"] = f"?ULG__{identifier}?"

        elif not game_exists and game_attrs["title"] == "Fancade":  # has no image and no title
            await submissionutils.send_error_embed(
                interaction,
                "Hmm, either that game doesn't exist or it hasn't been processed yet."
            )
            return None

        if member is None or member == interaction.user:
            embed = submissionutils.create_embed_with_author(
                discord.Color.blue(),
                f"{self.bot.config['loading_emoji']} Processing submission...",
                interaction.user,
                interaction.user.avatar.url
            )
            await interaction.response.send_message(embed=embed)

            post = {
                "guild_id": interaction.guild_id,
                "author_id": interaction.user.id,
                "title": game_attrs["title"],
                "link": link
            }
            await self.db.insert_one(post)

            embed.description = f"{interaction.user.mention}, your game **{game_attrs['title']}** was submitted successfully."
            embed.set_thumbnail(url=game_attrs["image_url"])
            await interaction.edit_original_response(embed=embed)

        elif member is not None or member != interaction.user:
            embed = submissionutils.create_embed_with_author(
                discord.Color.blue(),
                f"{self.bot.config['loading_emoji']} Processing submission...",
                interaction.user,
                interaction.user.avatar.url
            )
            await interaction.response.send_message(embed=embed)

            post = {
                "guild_id": interaction.guild_id,
                "author_id": member.id,
                "title": game_attrs["title"],
                "link": link
            }
            await self.db.insert_one(post)

            embed.description = f"{interaction.user.mention}, the game **{game_attrs['title']}** was submitted successfully."
            embed.set_thumbnail(url=game_attrs["image_url"])
            embed.set_footer(text=f"Submitted for {member}", icon_url=member.avatar.url)
            await interaction.edit_original_response(embed=embed)


    @submissions_group.command(name="unsubmit", description="Unsubmits your game from the database")
    @app_commands.describe(link="Your game's link, you can get this by sharing your game in Fancade.")
    async def unsubmit_command(self, interaction: discord.Interaction, link: str) -> None:

        if not link.startswith("https://play.fancade.com/"):
            await submissionutils.send_error_embed(interaction, "Sorry, but I don't recognize that link.")
            return None

        can_manage_guild = interaction.user.guild_permissions.manage_guild
        document = await self.db.find_one({"guild_id": interaction.guild_id, "link": link})

        if document is None:
            await submissionutils.send_error_embed(interaction, "Sorry, but I can't find that game in the database.")
            return None

        author = await interaction.guild.fetch_member(document["author_id"])
        view = Confirm(interaction.user)

        if author.id != interaction.user.id:
            if not can_manage_guild:
                await submissionutils.send_error_embed(
                    interaction,
                    "Sorry, but you can't unsubmit another member's submission since you're missing `Manage Server` permission."
                )
                return None

            embed = submissionutils.create_embed_with_author(
                discord.Color.orange(),
                f"This will delete the submission **{document['title']}** which was submitted by **{author}**. Are you sure you wanna proceed?",
                interaction.user,
                interaction.user.avatar.url
            )
            await interaction.response.send_message(embed=embed, view=view)

            await submissionutils.handle_confirm_view(
                self.bot.config, self.db, interaction, view, {"guild_id": interaction.guild.id, "link": link}, document
            )

        if author.id == interaction.user.id:
            embed = submissionutils.create_embed_with_author(
                discord.Color.orange(),
                f"This will delete your submission **{document['title']}**. Are you sure you wanna proceed?",
                interaction.user,
                interaction.user.avatar.url
            )
            await interaction.response.send_message(embed=embed, view=view)

            await submissionutils.handle_confirm_view(
                self.bot.config, self.db, interaction, view, {"guild_id": interaction.guild.id, "link": link}, document
            )


    @unsubmit_command.autocomplete("link")
    async def unsubmit_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:

        if interaction.user.guild_permissions.manage_guild:
            post = {"title": {"$regex": current}, "guild_id": interaction.guild.id}
            results = await self.db.find(post)
            results.sort(key=lambda x: x["author_id"])
            return [
                app_commands.Choice(
                    name=f"{result['title']} by {await interaction.guild.fetch_member(result['author_id'])}",
                    value=result["link"]
                ) for result in results
            ]
        else:
            post = {"title": {"$regex": current}, "guild_id": interaction.guild.id, "author_id": interaction.user.id}
            results = await self.db.find(post)
            results.sort(key=lambda x: x["author_id"])
            return [
                app_commands.Choice(name=result['title'], value=result["link"]) for result in results
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

        if show_all:
            post = {"guild_id": interaction.guild.id}
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            user = None

        elif member is None or member == interaction.user:
            post = {"guild_id": interaction.guild.id, "author_id": interaction.user.id}
            no_submission_message = "You haven't submitted anything yet."
            show_all = False
            user = interaction.user

        elif member is not None or member != interaction.user:
            post = {"guild_id": interaction.guild.id, "author_id": member.id}
            no_submission_message = f"**{member}** hasn't submitted anything yet."
            show_all = False
            user = member

        documents = await self.db.find(post)
        documents.sort(key=lambda x: x["author_id"])

        if not documents:
            await submissionutils.send_error_embed(interaction, no_submission_message)
            return None

        embed = submissionutils.create_embed_with_author(
            discord.Color.blue(),
            f"{self.bot.config['loading_emoji']} Loading submissions...",
            interaction.user,
            interaction.user.avatar.url
        )
        await interaction.response.send_message(embed=embed)

        embeds = await submissionutils.create_submissions_embed(interaction, documents, user, show_all)
        paginator = EmbedPaginator(interaction, embeds, documents)

        if paginator.max_pages > 1:
            paginator.next.disabled = False

        embed = embeds[0]
        embed.set_footer(
            text=f"Page {paginator.current_page + 1}/{paginator.max_pages} • Total amount of submissions: {len(documents)}"
        )
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

        can_manage_guild = interaction.user.guild_permissions.manage_guild

        if clear_all:
            post = {"guild_id": interaction.guild.id}
            no_submission_message = "Hmm, it seems like nobody has submitted anything yet."
            success_message = "All submissions have been deleted."
            confirm_message = "This will delete everyone's submissions. Are you sure you wanna proceed?"

            if not can_manage_guild:
                await submissionutils.send_error_embed(interaction, "Sorry, but you are missing `Manage Server` permission.")
                return None

        elif member is None or member == interaction.user:
            post = {"guild_id": interaction.guild.id, "author_id": interaction.user.id}
            no_submission_message = "You haven't submitted anything yet."
            success_message = "Deleted all of your submissions."
            confirm_message = "This will delete all of your submissions. Are you sure you wanna proceed?"

        elif member is not None or member != interaction.user:
            post = {"guild_id": interaction.guild.id, "author_id": member.id}
            no_submission_message = f"**{member}** hasn't submitted anything yet."
            success_message = f"Deleted all of **{member}**'s submissions."
            confirm_message = f"This will delete all of **{member}**'s submissions. Are you sure you wanna proceed?"

            if not can_manage_guild:
                await submissionutils.send_error_embed(interaction, "Sorry, but you are missing `Manage Server` permission.")
                return None

        documents = await self.db.find(post)
        if not documents:
            await submissionutils.send_error_embed(interaction, no_submission_message)
            return None

        view = Confirm(interaction.user)

        embed = submissionutils.create_embed_with_author(
            discord.Color.orange(),
            confirm_message,
            interaction.user,
            interaction.user.avatar.url
        )
        await interaction.response.send_message(embed=embed, view=view)

        await submissionutils.handle_confirm_view(
            self.bot.config, self.db, interaction, view, post, documents, success_message, True
        )


    @app_commands.command(name="getsource", description="Gets the source of the file and sends it to you.")
    @app_commands.describe(file_name="The name of the file you want to get the source of.")
    async def get_source(self, interaction: discord.Interaction, file_name: str) -> None:
        if not file_name in self.open_source_files:
            await submissionutils.send_error_embed(interaction, "Sorry, but you either can't access that file or it doesn't exist.")
            return None

        with open(file_name, "r") as f:
            buffer = BytesIO(f.read().encode("utf8"))

        file = discord.File(buffer, file_name)
        await interaction.response.send_message(file=file)


    @get_source.autocomplete("file_name")
    async def get_source_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=source_name, value=source_name) for source_name in self.open_source_files
        ]
        

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Submission(bot))
