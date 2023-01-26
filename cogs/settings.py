import logging

import discord
from discord.ext import commands

import config
from utils import autocompletes, check, db


log = logging.getLogger("mainLog")


class SettingsSelectView(discord.ui.View):
    def __init__(self, author):
        self.author = author
        super().__init__(timeout=300, disable_on_timeout=True)

    @discord.ui.string_select(options=autocompletes.settings)
    async def select_option(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error", description="You may not use this option", color=discord.Color.brand_red()
                ),
                ephemeral=True,
            )
        select.disabled = True
        select.placeholder = str(select.values[0])
        await interaction.message.edit(view=self)
        match select.values[0]:
            case "statistics":

                em = discord.Embed(title="Select a channel for you statistics", color=discord.Color.dark_gold())

                return await interaction.response.send_message(embed=em, view=StatisticsSelect())
            case "volume":
                return await interaction.response.send_modal(VolumeModal())

            case _:
                return None


class StatisticsSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300, disable_on_timeout=True)

    @discord.ui.channel_select(channel_types=[discord.ChannelType.text])
    async def statistics_select(self, select: discord.ui.Select, interaction: discord.Interaction):
        # TODO: send a message, fetch the message id, save the channel/message id to edit the message!
        select.placeholder = select.values[0].name
        select.disabled = True
        await self.message.edit(view=self)
        db_return = await db.insert_settings(
            setting_name="statistics", setting=select.values[0].id, guild=interaction.guild_id
        )
        if db_return is None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Success",
                    description=f"Set the statistics channel to {select.values[0].mention}",
                    color=discord.Color.brand_green(),
                ),
                ephemeral=True,
            )
        elif int(db_return[0]) == select.values[0].id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Success",
                    description=f"Channel already was {select.values[0].mention}, nothing changed",
                    color=discord.Color.brand_green(),
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Success",
                    description=f"Changed the statistics channel from <#{db_return[0]}> to {select.values[0].mention}",
                    color=discord.Color.brand_green(),
                ),
                ephemeral=True,
            )


class VolumeModal(discord.ui.Modal):
    def __init__(self, title: str = "Volume"):
        self.title = title
        super().__init__(title=self.title)
        self.add_item(discord.ui.InputText(label="Set the Volume", min_length=1, max_length=4, value="25"))

    async def callback(self, interaction: discord.Interaction):
        try:
            number = int(self.children[0].value)
        except ValueError:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="Please enter a valid number betweeen 1 and 1000",
                    color=discord.Color.brand_red(),
                ),
                ephemeral=True,
            )

        if not number > 0 and number <= 1000:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="Please enter a valid number betweeen 1 and 1000",
                    color=discord.Color.brand_red(),
                ),
                ephemeral=True,
            )

        db_return = await db.insert_settings(setting_name="volume", setting=number, guild=interaction.guild_id)
        if db_return is None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Success", description=f"Set the volume to {number}%", color=discord.Color.brand_green()
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Success",
                    description=f"Changed the volume from {db_return[0]}% to {number}%",
                    color=discord.Color.brand_green(),
                ),
                ephemeral=True,
            )


class Settings(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        log.debug("Started Settings Cog")

    @commands.slash_command(name="settings", description="set configs for the bot")
    async def settings(self, ctx: discord.ApplicationContext):
        member = ctx.guild.get_member(ctx.user.id)
        role = ctx.guild.get_role(config.TEAM_ROLE)
        if await check.has_role(member=member, role=role):
            em = discord.Embed(title="Select what you want to edit", color=discord.Color.dark_gold())
            await ctx.response.send_message(embed=em, view=SettingsSelectView(ctx.author))
        else:
            em = discord.Embed(
                title="Error",
                description=f"You may  not user this command required role: {role.mention}",
                color=discord.Color.brand_red(),
            )
            await ctx.response.send_message(embed=em, ephemeral=True)


def setup(client):
    client.add_cog(Settings(client))
