import logging
import humanize
import discord
from pathlib import Path
from discord.ext import commands
from discord import app_commands

from cogs.utils.config import Config
from cogs.utils.modals import ReportUserModal


abs_path = Path(__file__).parent.resolve()


class Bot(commands.Bot):

    def __init__(self):

        # bot variables
        self.uptime = discord.utils.utcnow()
        self._cogs = [p.stem for p in Path(".").glob("./cogs/*.py")]
        self.cmd_prefix = "ob."

        # logging
        self.log = logging.getLogger("discord")
        self.log.setLevel(logging.INFO)

        # utils
        self.config = Config()

        super().__init__(
            command_prefix=self.cmd_prefix,
            owner_ids=Config.OWNER_IDS,
            activity=discord.Activity(type=discord.ActivityType.playing, name="with new features."),
            intents=discord.Intents.all()
        )

        # context menus
        self.report_user_ctx_menu = app_commands.ContextMenu(
            name="Report User",
            callback=self.report_user,
            guild_ids=[self.config.TEST_GUILD_ID.id]
        )
        self.tree.add_command(self.report_user_ctx_menu)


    # context menus
    async def report_user(self, interaction: discord.Interaction, member: discord.Member):

        if member == interaction.user:
            await interaction.response.send_message("Hey! You can't report yourself!", ephemeral=True)
            return None
        
        report_guild = discord.utils.get(self.guilds, id=self.config.REPORT_GUILD_ID)
        await interaction.response.send_modal(ReportUserModal(member, self.config.REPORT_CHANNEL_ID, report_guild))


    # built-in events and methods
    async def setup_hook(self):
        for cog in self._cogs:
            await self.load_extension(f"cogs.{cog}")
            self.log.info(f"Extension '{cog}' has been loaded.")

        await self.load_extension("jishaku")


    async def on_connect(self):
        self.log.info(f"Connected to Client (version: {discord.__version__}).")


    async def on_ready(self):
        self.log.info(f"Bot has connected (Guilds: {len(self.guilds)}) (Bot Username: {self.user.name}#{self.user.discriminator}) (Bot ID: {self.user.id}).")
        runtime = discord.utils.utcnow() - self.uptime
        self.log.info(f"connected after {humanize.precisedelta(runtime)}.")


    async def on_disconnect(self):
        self.log.critical("Bot has disconnected!")
