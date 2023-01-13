"""
Poll commands for Odd Bot.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import TYPE_CHECKING, Optional
from collections import Counter

import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.utils.embed import send_error_embed
from cogs.utils.app_commands import Group
from cogs.utils.time import str_to_timedelta

if TYPE_CHECKING:
    from bot import OddBot


RED_TICK = "<:e:1063144718059442307>"
    

async def check_poll(bot: "OddBot", _message_id: Optional[int] = None) -> None:
    async with bot.pool.acquire() as connection:
        if _message_id is not None:  # ending early
            end_early = True
            result = await connection.fetchrow(
                "SELECT message_id, channel_id FROM poll WHERE message_id = $1;",
                _message_id    
            )
        else:
            end_early = False
            now_unix_timestamp = discord.utils.utcnow().timestamp()
            result = await connection.fetchrow(
                "SELECT message_id, channel_id FROM poll WHERE deadline < $1;",
                now_unix_timestamp
            )

        if result is None:  # no poll
            return None

        if end_early:
            _, channel_id = result
            message_id = _message_id
        else:
            message_id, channel_id = result

        channel = bot.get_channel(channel_id)

        assert message_id
        try:
            assert isinstance(channel, discord.TextChannel)
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await connection.execute("DELETE FROM poll WHERE message_id = $1", message_id)
            return None

        option = await connection.fetchrow(
            """
            WITH max_vote_count AS (
                SELECT MAX(vote_count) FROM (
                    SELECT COUNT(poll_votes.id) AS vote_count
                    FROM poll_options
                    JOIN poll ON poll_options.poll_id = poll.id
                    JOIN poll_votes ON poll_options.id = poll_votes.option_id
                    WHERE poll.message_id = $1
                    GROUP BY poll_options.id
                ) temp
            )
            SELECT option_emoji, option_text, vote_count FROM (
                SELECT poll_options.option_emoji, poll_options.option_text, COUNT(poll_votes.id) AS vote_count
                FROM poll_options
                JOIN poll ON poll_options.poll_id = poll.id
                JOIN poll_votes ON poll_options.id = poll_votes.option_id
                WHERE poll.message_id = $1
                GROUP BY poll_options.id
            ) temp_table
            WHERE vote_count = (SELECT * FROM max_vote_count)
            ORDER BY RANDOM();
            """,
            message_id
        )

        if not option:  # no votes
            option = await connection.fetchrow(
                """
                SELECT option_emoji, option_text FROM poll_options 
                ORDER BY RANDOM()
                LIMIT 1;
                """
            )
            assert option
            field_value = f"{option['option_emoji']}**{option['option_text']}** has been chosen randomly since nobody voted on this poll."
        else:
            field_value = f"{option['option_emoji']}**{option['option_text']}** has won with a total of **`{option['vote_count']}`** votes!"

        await connection.execute("DELETE FROM poll WHERE message_id = $1", message_id)

    embed = discord.Embed(
        color=discord.Color.blue(),
        title="The theme has been chosen!",
        description=f"[Click here]({message.jump_url}) to jump to the poll."
    )
    embed.add_field(name="Poll results:", value=field_value)

    if end_early:
        embed.set_footer(text="This poll was force ended.")

    await message.edit(view=None)
    await channel.send(embed=embed)


class PollDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        super().__init__(placeholder="Select an option...", min_values=1, max_values=1, options=options, custom_id="poll:dropdown")

    async def callback(self, interaction: discord.Interaction):
        bot: OddBot = interaction.client # type: ignore
        selected_option = self.values[0]

        async with bot.pool.acquire() as connection:
            query = """
            SELECT poll.id AS poll_id, poll_options.id AS poll_options_id,
                poll_options.option_emoji, poll_options.option_text
            FROM poll
            JOIN poll_options ON poll.id = poll_options.poll_id
            LEFT JOIN poll_votes ON poll_votes.option_id = poll_options.id AND
                poll_votes.member_id = $1
            WHERE poll.message_id = $2 AND poll_options.option_text = $3;
            """
            assert interaction.message
            result = await connection.fetchrow(
                query,
                interaction.user.id,
                interaction.message.id,
                selected_option
            )
            if result is None:
                return None

            query = """
            INSERT INTO poll_votes (member_id, poll_id, option_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (member_id, poll_id)
            DO UPDATE SET option_id = $3;
            """
            await connection.execute(query, interaction.user.id, result["poll_id"], result["poll_options_id"])
            description = f"You voted for {result['option_emoji']}**{result['option_text']}**"
                
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=description
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PollView(discord.ui.View):
    def __init__(self, bot: "OddBot", options: Optional[dict[str, str]] = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.options = options
        self.add_dropdown()

    def add_dropdown(self) -> None:
        if self.options is None:
            return None

        dropdown = PollDropdown()
        for emoji, option in self.options.items():
            dropdown.options.append(discord.SelectOption(label=option, emoji=emoji))

        self.add_item(dropdown)

    @discord.ui.button(label="End", style=discord.ButtonStyle.danger, emoji=RED_TICK, custom_id="exit:button", row=1)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.message
        if interaction.user.guild_permissions.manage_guild:
            await check_poll(self.bot, interaction.message.id)
            await interaction.response.send_message("You force ended the poll.", ephemeral=True)
            return None

        await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)


class Poll(commands.Cog):

    __slots__ = "bot", "log"

    def __init__(self, bot: "OddBot"):
        self.bot = bot
        self.log = bot.log
        self.emojis = [
            "<:e:1062755730530254918>", "<:e:1062755732224737411>",
            "<:e:1062755725383831684>", "<:e:1062755743733907497>",
            "<:e:1062755746942558268>", "<:e:1062755726923141201>",
            "<:e:1062755738814009375>", "<:e:1062755722233917541>"
        ]
        self.poll_loop.start()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.log.info(f"{self.__class__.__name__.lower()} module is ready.")

    poll_group = Group(name="poll", description="Poll related commands.")

    @poll_group.command(name="create", description="Creates a poll (max 8 options)")
    @app_commands.describe(
        _deadline="When the poll is going to end.",
        _options="Your poll options, make sure to separate each options with a comma. (should be 2 or more options.)",
        channel="Where you want to send this poll."
    )
    @app_commands.rename(_deadline="deadline", _options="options")
    async def poll_create(
    self,
    interaction: discord.Interaction,
    _deadline: str,
    _options: str,
    channel: Optional[discord.TextChannel] = None
    ) -> None:

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"{self.bot.config['loading_emoji']} Creating poll..."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        assert isinstance(interaction.channel, discord.TextChannel)
        channel = interaction.channel if channel is None else channel

        options = list(filter(lambda x: x, [option.strip() for option in _options.split(",")]))
        option_counts = Counter(options)

        if [item for item, count in option_counts.items() if count > 1]:
            await send_error_embed(interaction, "Please don't duplicate your option texts.")
            return None

        if len(options) < 2:
            await send_error_embed(interaction, "Please put 2 or more options.")
            return None

        if len(options) > 8:
            await send_error_embed(interaction, "The amount of options cannot exceed 8.")
            return None

        if any(map(lambda x: len(x) > 100, options)):
            await send_error_embed(interaction, "Each option's text cannot exceed 100 characters.")
            return None

        deadline = str_to_timedelta(_deadline)
        if deadline is None:
            await send_error_embed(interaction, f"{_deadline} cannot be converted.")
            return None

        deadline = discord.utils.utcnow() + deadline
        deadline_unix_timestamp = deadline.timestamp()

        opts = {}
        for i, option in enumerate(options):
            opts[self.emojis[i]] = option

        description = f"Poll deadline: {discord.utils.format_dt(deadline, style='F')}\n\n"
        for emoji, option in opts.items():
            description += f"{emoji} **{option}**\n"

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=description,
            title="Choose the theme for next week."
        )
        assert interaction.guild
        assert interaction.guild.icon
        embed.set_author(name=interaction.guild, icon_url=interaction.guild.icon.url)
        embed.set_footer(text=f"Poll created by {interaction.user}")

        message = await channel.send(embed=embed, view=PollView(self.bot, opts))

        async with self.bot.pool.acquire() as connection:
            poll_id = await connection.fetchval(
                """
                INSERT INTO poll (message_id, channel_id, deadline) VALUES ($1, $2, $3)
                RETURNING id;
                """,
                message.id,
                channel.id,
                deadline_unix_timestamp
            )

            await connection.executemany(
                "INSERT INTO poll_options (poll_id, option_emoji, option_text) VALUES ($1, $2, $3);",
                [(poll_id, emoji, option) for (emoji, option) in opts.items()]
            )

        embed = discord.Embed(
            color=discord.Color.green(),
            description="Your poll has been created."
        )
        await interaction.edit_original_response(embed=embed)

    @poll_group.command(name="end", description="Force ends an existing poll")
    @app_commands.describe(
        message_id="The ID of the poll you want to end, or you can just press the end button."
    )
    async def poll_end(self, interaction: discord.Interaction, message_id: str) -> None:
        async with self.bot.pool.acquire() as connection:
            result = await connection.fetchrow("SELECT message_id FROM poll WHERE message_id = $1", int(message_id))

        await check_poll(self.bot, int(message_id))
        if result is None:
            await interaction.response.send_message("This poll does not exist.", ephemeral=True)
        else:
            await interaction.response.send_message("You force ended this poll.", ephemeral=True)

    @tasks.loop(seconds=5.0)
    async def poll_loop(self):
        await self.bot.wait_until_ready()
        await check_poll(self.bot)

        
async def setup(bot: "OddBot") -> None:
    await bot.add_cog(Poll(bot))
