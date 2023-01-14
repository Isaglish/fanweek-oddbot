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

from cogs.utils.embed import create_embed_with_author

if TYPE_CHECKING:
    from bot import OddBot


class HelpCommandDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Text commands", description="Commands invoked with a prefix.", emoji="📜"),
            discord.SelectOption(label="Slash commands", description='Commands invoked with the "/" (slash) key.', emoji="<:graytick:1023711792385503283>"),
            discord.SelectOption(label="Context menus", description="Commands invoked by accessing the context menu.", emoji="🔘")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

        self.text_commands = [
            "sync [option: None]",
            "jishaku"
        ]

    async def callback(self, interaction: discord.Interaction) -> None:
        bot: OddBot = interaction.client # type: ignore

        selected = self.values[0]
        if selected == "Text commands":
            commands = [f"**{i+1}.** `{bot.cmd_prefix}{cmd}`" for i, cmd in enumerate(self.text_commands)]

            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="\n".join(commands),
                author=interaction.user
            )

        elif selected == "Slash commands":
            commands = [f"**{i+1}.** `/{cmd.qualified_name}`" for i, cmd in enumerate(bot.tree.walk_commands())]
            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="\n".join(commands),
                author=interaction.user
            )

        else:
            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="**1.** `Report User`",
                author=interaction.user
            )

        assert embed.description
        embed.description += "\n\nCheckout the features here on [GitHub](https://github.com/Isaglish/fanweek-oddbot#features)."
        await interaction.response.edit_message(embed=embed, view=HelpCommandDropdownView(interaction.user))


class HelpCommandDropdownView(discord.ui.View):
    def __init__(self, author: discord.Member | discord.User):
        self.author = author
        super().__init__()
        self.add_item(HelpCommandDropdown())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False

        return True


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
            database_version = await connection.fetchval("SELECT version();")
            assert database_version

            database_uptime = await connection.fetchval(
                "SELECT extract(epoch FROM now() - pg_postmaster_start_time())::integer AS uptime;"
            )
            assert database_uptime

            database_size = await connection.fetchval("SELECT pg_size_pretty(pg_database_size(current_database()));")
            assert database_size

            active_connections = await connection.fetchval(
                """
                SELECT active_connections FROM (
                    SELECT count(pid) AS active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active'
                ) active_connections;
                """
            )
            assert active_connections

        bot_uptime = discord.utils.format_dt(self.bot.uptime, style="R")
        database_uptime = discord.utils.format_dt(
            discord.utils.utcnow() - timedelta(seconds=database_uptime),
            style="R"
        )

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name="Bot Info.")
        embed.add_field(
            name="Versions:",
            value=f"• **Python:** {python_version}\n• **Discord.py:** {discord_version}\n• **Database:** {database_version[:16]}",
            inline=False
        )

        embed.add_field(
            name="Uptime:",
            value=f"• **Bot**: {bot_uptime}\n• **Database:** {database_uptime}",
            inline=False
        )

        embed.add_field(
            name="Database:",
            value=f"• **Size:** {database_size}\n• **Active Connections:** {active_connections}"
        )

        embed.add_field(
            name="Latency:",
            value=f"• **Websocket:** {round(self.bot.latency * 1000)}ms",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: "OddBot") -> None:
    await bot.add_cog(Info(bot))