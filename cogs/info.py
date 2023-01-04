"""
Information commands for Odd Bot.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import sys
from typing import TYPE_CHECKING
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from cogs.utils.dropdown import HelpCommandDropdownView

if TYPE_CHECKING:
    from bot import OddBot


class Info(commands.Cog):

    __slots__ = "bot", "log"

    def __init__(self, bot: "OddBot"):
        self.bot = bot
        self.log = bot.log


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.log.info(f"{self.__class__.__name__.lower()} module is ready.")


    @app_commands.command(name="help", description="A help command that shows all available features.")
    async def help_command(self, interaction: discord.Interaction) -> None:

        description = f"""
        Hello there! Welcome to the help page.

        Use the dropdown menu below to select a category.

        **Who are you?**
        I'm a bot made by Isaglish#8034. I was created on
        <t:1614414925:F>.
        I was made specifically for Fanweek and for keeping track of your submissions.
        You could get more information by using the dropdown below.

        I am also open-source so come check out my code on [GitHub](https://github.com/Isaglish/fanweek-oddbot)!
        """
        embed = discord.Embed(color=discord.Color.blue(), description=description)
        embed.set_author(name="Bot Help Page.")

        view = HelpCommandDropdownView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view)


    @app_commands.command(name="info", description="Different bot related informations.")
    async def info_command(self, interaction: discord.Interaction) -> None:

        # versions
        python_version = sys.version[:7]
        discord_version = discord.__version__

        async with self.bot.pool.acquire() as connection:
            database_version = await connection.fetchrow("SELECT version()")
            assert database_version

            database_uptime = await connection.fetchrow(
                "SELECT extract(epoch FROM now() - pg_postmaster_start_time())::integer AS uptime"
            )
            assert database_uptime

            database_size = await connection.fetchrow("SELECT pg_size_pretty(pg_database_size(current_database()))")
            assert database_size

            database_connections = await connection.fetchrow("SELECT count(*) FROM pg_stat_activity")
            assert database_connections

        bot_uptime = discord.utils.format_dt(self.bot.uptime, style="R")
        database_uptime = discord.utils.format_dt(
            discord.utils.utcnow() - timedelta(seconds=database_uptime['uptime']),
            style="R"
        )

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name="Bot Info.")
        embed.add_field(
            name="Versions:",
            value=f"**Python:** {python_version}\n**Discord:** {discord_version}\n**Database:** {database_version['version'][:16]}",
            inline=False
        )

        embed.add_field(
            name="Uptime:",
            value=f"**Bot**: {bot_uptime}\n**Database:** {database_uptime}",
            inline=False
        )

        embed.add_field(
            name="Database:",
            value=f"**Size:** {database_size['pg_size_pretty']}\n**Connections:** {database_connections['count']}"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: "OddBot") -> None:
    await bot.add_cog(Info(bot))