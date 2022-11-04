"""
Select menu objects for dropdowns.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

from typing import TYPE_CHECKING

import discord

from cogs.utils.embed import create_embed_with_author

if TYPE_CHECKING:
    from bot import OddBot


__all__ = (
    "HelpCommandDropdown",
    "HelpCommandDropdownView"
)


class HelpCommandDropdown(discord.ui.Select):

    def __init__(self) -> None:
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
        