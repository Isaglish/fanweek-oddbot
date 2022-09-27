"""
Select menu objects for dropdowns.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import discord

from cogs.utils.embed import create_embed_with_author


class HelpCommandDropdown(discord.ui.Select):

    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="Text commands", description="Commands invoked with a prefix.", emoji="📜"),
            discord.SelectOption(label="Slash commands", description='Commands invoked with the "/" (slash) key.', emoji="<:graytick:1023711792385503283>"),
            discord.SelectOption(label="Context menus", description="Commands invoked by accessing the context menu.", emoji="🔘")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    
    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]
        if selected == "Text commands":

            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="**Text Commands:**\n\n**1.** `ob.sync [option]`\n**2.** `ob.jsk [command] | ob.jishaku [command]`",
                author=interaction.user
            )

        elif selected == "Slash commands":
            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="**Slash Commands:**\n\n**1.** `/submissions submit <link> [member]`\n**2.** `/submissions unsubmit <link>`\n**3.** `/submissions show [all]`\n**4.** `/submissions clear [member] [all]`\n**5.** `/help`\n**6.** `/getsource <file_name>`",
                author=interaction.user
            )

        else:
            embed = create_embed_with_author(
                color=discord.Color.blue(),
                description="**Context Menus:**\n\n**1.** `Report User`",
                author=interaction.user
            )

        assert embed.description
        embed.description += "\n\nCheckout the features here on [GitHub](https://github.com/Isaglish/fanweek-oddbot#features)."
        await interaction.response.edit_message(embed=embed, view=HelpCommandDropdownView())


class HelpCommandDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpCommandDropdown())

