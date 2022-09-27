"""
Classes for discord views.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord


__all__ = (
    "Confirm",
    "EmbedPaginator"
)


class Confirm(discord.ui.View):

    __slots__ = "value", "author"

    def __init__(self, author: discord.Member) -> None:
        super().__init__()
        self.value = None
        self.author = author
        

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = True
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = False
        self.stop()


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False
           
        return True


class EmbedPaginator(discord.ui.View):

    __slots__ = "interaction", "author", "embeds", "current_page", "max_pages"

    def __init__(self, interaction: discord.Interaction, embeds: list[discord.Embed]) -> None:
        super().__init__(timeout=None)
        self.current_page = 0
        self.max_pages = len(embeds)
        self.interaction = interaction
        self.author = interaction.user
        self.embeds = embeds


    @property
    def index_page(self) -> discord.Embed:
        if self.max_pages > 1:
            self.next.disabled = False

        embed = self.embeds[0]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        return embed


    @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.blurple, custom_id="prev_page:button", disabled=True)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = self.current_page - 1 == 0
        self.next.disabled = False
        self.current_page -= 1
        
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)


    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.blurple, custom_id="next_page:button", disabled=True)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = self.current_page + 1 == self.max_pages - 1
        self.prev.disabled = False
        self.current_page += 1

        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)


    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red, custom_id="quit:button")
    async def quit_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=None)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False

        return True
