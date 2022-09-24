"""
Classes for discord modals

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import traceback

import discord

from .embed import create_embed_with_author


__all__ = (
    "ReportUserModal",
)


class ReportUserModal(discord.ui.Modal):

    __slots__ = "member", "channel_id", "guild"

    def __init__(self, member: discord.Member, channel_id: discord.TextChannel, guild: discord.Guild) -> None:
        self.member = member
        self.channel_id = channel_id
        self.guild = guild

        super().__init__(title="Report User", custom_id="report_user_modal")


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
        report_channel = await self.guild.fetch_channel(self.channel_id)

        embed = create_embed_with_author(
            discord.Color.red(),
            f"**Reported User**: {self.member.mention}\n**User ID**: {self.member.id}\n\n**Reason for reporting**: {self.name.value}\n**Description**: {self.description.value}",
            interaction.user,
        )
        await report_channel.send(embed=embed)


    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Erm.. Something went wrong.", ephemeral=True)

        traceback.print_tb(error.__traceback__)

