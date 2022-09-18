import discord
import aiohttp
from bs4 import BeautifulSoup


class SubmissionHelper:

    @staticmethod
    async def get_game_attrs(link: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                r = await response.text()
                doc = BeautifulSoup(r, "html.parser")
                title = doc.find("title").text
                author = doc.find("p", class_="author").text
                image_url = doc.find("meta", attrs={"property": "og:image"}).attrs["content"]
                description = doc.find("meta", attrs={"name": "description"}).attrs["content"]

        return {"title": title, "image_url": image_url, "description": description, "author": author}


    @staticmethod
    async def send_error_message(interaction: discord.Interaction, message: str):
        embed = discord.Embed(color=discord.Color.red(), description=message)
        embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
        try:
            await interaction.response.send_message(embed=embed)
        except discord.InteractionResponded:
            await interaction.edit_original_response(embed=embed)


    @staticmethod
    async def create_submissions_embed(interaction: discord.Interaction, query: list, member: discord.Member = None, show_all: bool = True):
        embeds = []
        k = 10
        for i in range(0, len(query), 10):
            current = query[i:k]
            k += 10

            number = i
            infos = []
            for submission in current:
                number += 1
                user = await interaction.guild.fetch_member(submission["author_id"])

                if show_all:
                    infos.append(f"**{number}.** [{submission['title']}]({submission['link']}) • {user}")
                else:
                    infos.append(f"**{number}.** [{submission['title']}]({submission['link']})")

            info = "\n".join(infos)

            if show_all:
                embed = discord.Embed(color=discord.Color.blue(), description=f"**Showing all submissions:**\n\n{info}")
                embed.set_author(name=f"{interaction.guild} Submissions", icon_url=interaction.guild.icon.url)
            else:
                embed = discord.Embed(color=discord.Color.blue(), description=f"**Showing all of {member}'s submissions:**\n\n{info}")
                embed.set_author(name=f"{interaction.user}", icon_url=interaction.user.avatar.url)

            embeds.append(embed)

        return embeds
