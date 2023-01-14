"""
MIT License

Copyright (c) 2022 Isaglish

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
from typing import Any
from pathlib import Path
from typing import Literal, Optional
from traceback import print_tb

import discord
import asyncpg
from discord.ext import commands
from discord import app_commands

from cogs.poll import PollView
from cogs.utils import Context
from cogs.utils.embed import create_embed_with_author

__all__ = (
    "OddBot",
)

REPORT_CHANNEL_ID = 1020388867506962542
REPORT_GUILD_ID = 758487559399145524
OWNER_IDS = [353774678826811403]


class ReportUserModal(discord.ui.Modal):

    __slots__ = "member", "channel_id", "guild"

    def __init__(self, member: discord.Member, channel_id: int, guild: discord.Guild) -> None:
        super().__init__(title="Report User", custom_id="report_user_modal")
        self.member = member
        self.channel_id = channel_id
        self.guild = guild

    name = discord.ui.TextInput(
        label="Reason for reporting",
        placeholder="Your reason for reporting this user.",
        min_length=5,
        max_length=50
    )

    description = discord.ui.TextInput(
        label="Report description",
        style=discord.TextStyle.long,
        placeholder="Brief explanation of your report. Please note that false reports could get you punished.",
        required=True,
        min_length=15,
        max_length=1600
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Thank you for reporting! We will come back to you after reviewing the report.", ephemeral=True)

        report_channel = self.guild.get_channel(self.channel_id)

        assert isinstance(report_channel, discord.TextChannel)

        embed = create_embed_with_author(
            color=discord.Color.red(),
            description=f"**Reported User**: {self.member.mention}\n**User ID**: {self.member.id}\n\n**Reason for reporting**: {self.name.value}\n**Description**: {self.description.value}",
            author=interaction.user
        )
        await report_channel.send(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Erm.. Something went wrong.", ephemeral=True)
        print_tb(error.__traceback__)


class OddBot(commands.Bot):
    def __init__(self, config: dict[str, Any], cmd_prefix: str) -> None:
        # bot variables
        self.uptime = discord.utils.utcnow()
        self._cogs = [p.stem for p in Path(".").glob("./cogs/*.py")]
        self.cmd_prefix = cmd_prefix

        # logging
        self.log = logging.getLogger("discord")
        self.log.setLevel(logging.INFO)

        self.config = config

        super().__init__(
            command_prefix=cmd_prefix,
            owner_ids=OWNER_IDS,
            activity=discord.Activity(type=discord.ActivityType.playing, name="/help"),
            intents=discord.Intents.all(),
            help_command=None
        )

        # context menus
        self.report_user_ctx_menu = app_commands.ContextMenu(
            name="Report User",
            callback=self.report_user
        )
        self.tree.add_command(self.report_user_ctx_menu)
        self.add_command(sync)

    # context menus
    async def report_user(self, interaction: discord.Interaction, member: discord.Member) -> None:
        if member == interaction.user:
            await interaction.response.send_message("Hey! You can't report yourself!", ephemeral=True)
            return None

        report_guild = discord.utils.get(self.guilds, id=REPORT_GUILD_ID)
        assert report_guild
        await interaction.response.send_modal(ReportUserModal(member, REPORT_CHANNEL_ID, report_guild))

    # built-in events and methods
    async def setup_hook(self) -> None:
        for cog in self._cogs:
            await self.load_extension(f"cogs.{cog}")
            self.log.info(f"Extension '{cog}' has been loaded.")

        await self.load_extension("jishaku")
        await self.create_pool()
        await self.add_persistent_views()

    async def on_connect(self) -> None:
        self.log.info(f"Connected to Client (version: {discord.__version__}).")

    async def on_ready(self) -> None:
        assert self.user

        self.log.info(f"Bot has connected (Guilds: {len(self.guilds)}) (Bot Username: {self.user}) (Bot ID: {self.user.id}).")
        runtime = discord.utils.utcnow() - self.uptime
        self.log.info(f"connected after {runtime.total_seconds():.2f} seconds.")

    async def on_disconnect(self) -> None:
        self.log.critical("Bot has disconnected!")

    async def create_pool(self) -> None:
        pool = await asyncpg.create_pool(dsn=self.config["supabase_url"])
        assert pool
        async with pool.acquire() as connection:
            query = """
            CREATE TABLE IF NOT EXISTS submission (
                id SERIAL PRIMARY KEY,
                author_id BIGINT,
                guild_id BIGINT,
                game_title TEXT,
                game_url TEXT
            );

            CREATE TABLE IF NOT EXISTS poll (
                id SERIAL PRIMARY KEY,
                message_id BIGINT,
                channel_id BIGINT,
                deadline INTEGER
            );

            CREATE TABLE IF NOT EXISTS poll_options (
                id SERIAL PRIMARY KEY,
                poll_id INTEGER REFERENCES poll(id) ON DELETE CASCADE,
                option_emoji VARCHAR(100) NOT NULL,
                option_text VARCHAR(100) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS poll_votes (
                id SERIAL PRIMARY KEY,
                member_id BIGINT,
                poll_id INTEGER REFERENCES poll(id) ON DELETE CASCADE,
                option_id INTEGER REFERENCES poll_options(id) ON DELETE CASCADE,
                UNIQUE (member_id, poll_id)
            );
            """
            await connection.execute(query)

        self.pool = pool

    async def add_persistent_views(self) -> None:
        async with self.pool.acquire() as connection:
            options = await connection.fetch(
                """
                SELECT poll_id, ARRAY_AGG(option_emoji) as option_emoji, ARRAY_AGG(option_text) as option_text
                FROM poll_options
                GROUP BY poll_id;
                """
            )
            for _, option_emojis, option_texts in options:
                options_dict = {emoji: text for emoji, text in zip(option_emojis, option_texts)}
                self.add_view(PollView(self, options_dict))
        

# ungrouped commands
@commands.is_owner()
@commands.command()
async def sync(ctx: Context, option: Optional[Literal["~", "*", "^"]] = None) -> None:
    """Syncs all app commands to the server"""

    assert ctx.guild

    if option == "~":
        synced = await ctx.bot.tree.sync(guild=ctx.guild)  # sync to guild

    elif option == "*":
        ctx.bot.tree.copy_global_to(guild=ctx.guild)  # copy from global commands and sync to guild
        synced = await ctx.bot.tree.sync(guild=ctx.guild)

    elif option == "^":
        ctx.bot.tree.clear_commands(guild=ctx.guild)  # clear tree then sync
        await ctx.bot.tree.sync(guild=ctx.guild)
        synced = []

    else:
        synced = await ctx.bot.tree.sync()  # sync globally

    await ctx.send(f"Synced {len(synced)} commands {'globally' if option is None else 'to the current guild'}.")
