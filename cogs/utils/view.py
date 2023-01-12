"""
Classes for discord views.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord


__all__ = (
    "Confirm",
)

GREEN_CHECK = "<:e:1063144725915373688>"
RED_TICK = "<:e:1063144718059442307>"


class Confirm(discord.ui.View):

    __slots__ = "value", "author"

    def __init__(self, author: discord.Member, **kwargs):
        super().__init__(**kwargs)
        self.value = None
        self.author = author

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji=GREEN_CHECK)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji=RED_TICK)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False
           
        return True
        