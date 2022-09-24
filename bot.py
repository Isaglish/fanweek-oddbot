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
import json
from pathlib import Path
from typing import Any, Literal, Optional

import discord
from discord.ext import commands
from discord import app_commands

from cogs.utils import Context
from cogs.utils.modals import ReportUserModal


__all__ = (
    "Bot",
)


abs_path = Path(__file__).parent.resolve()


class Bot(commands.Bot):

    def __init__(self) -> None:

        # bot variables
        self.uptime = discord.utils.utcnow()
        self._cogs = [p.stem for p in Path(".").glob("./cogs/*.py")]
        self.cmd_prefix = "ob."

        # logging
        self.log = logging.getLogger("discord")
        self.log.setLevel(logging.INFO)

        self.config = self.load_config()

        super().__init__(
            command_prefix=self.cmd_prefix,
            owner_ids=self.config["owner_ids"],
            activity=discord.Activity(type=discord.ActivityType.playing, name="ob.help"),
            intents=discord.Intents.all(),
            help_command=None
        )

        # context menus
        self.report_user_ctx_menu = app_commands.ContextMenu(
            name="Report User",
            callback=self.report_user
        )
        self.tree.add_command(self.report_user_ctx_menu)

        self.add_command(help)
        self.add_command(sync)


    def load_config(self) -> dict[str, Any]:
        with open("config.json", "r") as f:
            config = json.load(f)

        return config


    # context menus
    async def report_user(self, interaction: discord.Interaction, member: discord.Member) -> None:

        if member == interaction.user:
            await interaction.response.send_message("Hey! You can't report yourself!", ephemeral=True)
            return None
        
        report_guild = discord.utils.get(self.guilds, id=self.config["report_guild_id"])

        assert report_guild

        await interaction.response.send_modal(ReportUserModal(member, self.config["report_channel_id"], report_guild))


    # built-in events and methods
    async def setup_hook(self) -> None:
        for cog in self._cogs:
            await self.load_extension(f"cogs.{cog}")
            self.log.info(f"Extension '{cog}' has been loaded.")

        await self.load_extension("jishaku")


    async def on_connect(self) -> None:
        self.log.info(f"Connected to Client (version: {discord.__version__}).")


    async def on_ready(self) -> None:
        assert self.user

        self.log.info(f"Bot has connected (Guilds: {len(self.guilds)}) (Bot Username: {self.user}) (Bot ID: {self.user.id}).")
        runtime = discord.utils.utcnow() - self.uptime
        self.log.info(f"connected after {runtime.total_seconds():.2f} seconds.")


    async def on_disconnect(self) -> None:
        self.log.critical("Bot has disconnected!")
        

# ungrouped commands
@commands.command()
async def help(ctx: Context) -> None:
    """Returns a link to the list of features the bot has."""
    await ctx.send("Here's the list of features:\nhttps://github.com/Isaglish/fanweek-oddbot#features")


@commands.is_owner()
@commands.command()
async def sync(ctx: Context, option: Optional[Literal["~", "*", "^"]] = None) -> None:
    """Syncs all app commands to the server"""

    assert ctx.guild

    if option == "~":
        synced = await ctx.bot.tree.sync(guild=ctx.guild)

    elif option == "*":
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await ctx.bot.tree.sync(guild=ctx.guild)

    elif option == "^":
        ctx.bot.tree.clear_commands(guild=ctx.guild)
        await ctx.bot.tree.sync(guild=ctx.guild)
        synced = []

    else:
        synced = await ctx.bot.tree.sync()

    await ctx.send(f"Synced {len(synced)} commands {'globally.' if option is None else 'to the current guild.'}")
