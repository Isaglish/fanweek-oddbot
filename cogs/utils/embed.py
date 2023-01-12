"""
Utility functions for embeds.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import Optional

import discord


__all__ = (
    "create_embed_with_author",
    "send_error_embed",
    "EmbedPaginator"
)

RIGHT_ARROW = "<:e:1063144722601885817>"
LEFT_ARROW = "<:e:1063144719812673556>"
RED_TICK = "<:e:1063144718059442307>"


def create_embed_with_author(
    color: discord.Color,
    description: str,
    author: str | discord.Member | discord.User,
    icon_url: Optional[str] = None
) -> discord.Embed:
    if not icon_url:
        if not isinstance(author, discord.Member):
            raise TypeError("Author doesn't have 'avatar' attribute.")

        assert author.avatar
        icon_url = author.avatar.url

    embed = discord.Embed(color=color, description=description)
    embed.set_author(name=author, icon_url=icon_url)

    return embed


async def send_error_embed(interaction: discord.Interaction, message: str) -> None:
    embed = create_embed_with_author(
        color=discord.Color.red(),
        description=message,
        author=interaction.user
    )
    try:
        await interaction.response.send_message(embed=embed)
    except discord.InteractionResponded:
        await interaction.edit_original_response(embed=embed)


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

    @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.blurple, custom_id="prev_page:button", disabled=True, emoji=LEFT_ARROW)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = self.current_page - 1 == 0
        self.next.disabled = False
        self.current_page -= 1
        
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.blurple, custom_id="next_page:button", disabled=True, emoji=RIGHT_ARROW)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        button.disabled = self.current_page + 1 == self.max_pages - 1
        self.prev.disabled = False
        self.current_page += 1

        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red, custom_id="quit:button", emoji=RED_TICK, row=2)
    async def quit_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author != interaction.user:
            await interaction.response.send_message("You don't have the permission to do that.", ephemeral=True)
            return False

        return True
        