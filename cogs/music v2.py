import asyncio
import logging
import datetime
import re
import typing

import discord
from discord.ext import commands, tasks
import wavelink
from wavelink.ext import spotify

import config
from utils import db, utility

log = logging.getLogger("mainLog")


async def play_or_queue(song, interaction: typing.Union[discord.Interaction, discord.Message]):
    if isinstance(interaction, discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect(cls = wavelink.Player)
    else:
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            vc = await interaction.author.voice.channel.connect(cls = wavelink.Player)
    em = discord.Embed(
        title = f"Now playing {song.title}",
        url = song.uri,
        description = f"""
    By: {song.author}
    Duration: {utility.sec_to_min(song.length)}
    """,
        color = discord.Color.blurple(),
    )
    em.set_image(url = song.thumbnail)
    if vc.is_playing():
        await vc.queue.put_wait(song)
    else:
        await vc.queue.put_wait(song)
        song = vc.queue.get()
        await vc.play(song)
    return em


async def edit_panel(vc: wavelink.Player, song: wavelink.YouTubeTrack = None):
    channel_id_db = await db.get_setting(setting_name = "panel_channel", guild_id = vc.guild.id)
    msg_id_db = await db.get_setting(setting_name = "panel_msg", guild_id = vc.guild.id)
    channel_id = channel_id_db[0]
    msg_id = msg_id_db[0]
    panel = await utility.fetch_or_get_message(client = vc.client, message_id = msg_id, channel_id = channel_id)
    embed = panel.embeds[0].to_dict()
    if song is None:
        embed = discord.Embed.from_dict(embed)
        embed.clear_fields()
    else:
        embed = discord.Embed(
            title = f"Now playing {song.title}",
            description = f"**By: {song.author}\nDuration: {utility.sec_to_min(song.length)}**",
            color = discord.Color.blurple(),
            timestamp = datetime.datetime.now(),
            url = song.uri,
        )
    try:
        embed.set_image(url = song.thumbnail)
    except AttributeError:
        pass
    try:
        queue = vc.queue.copy()
        duration_upcoming = vc.queue.copy()
        total_duration = 0
        for track in duration_upcoming:
            total_duration += track.duration
        embed.set_footer(text = f"Total duration: {utility.sec_to_min(total_duration)}")
        i = 0
        for next_track in queue:
            i += 1
            embed.add_field(
                name = f"{i}. in queue",
                value = f"[{next_track.title}]({next_track.uri})\n-> {next_track.author} :notes:\n-> {utility.sec_to_min(next_track.length)}  :hourglass_flowing_sand:",
                inline = False
            )
            if i >= 5:
                break
        queue = None
    except wavelink.QueueEmpty:
        pass
    await panel.edit(content = None, embed = embed, view = PanelView())


# noinspection PyTypeChecker
class SelectSongView(discord.ui.View):
    def __init__(self, songs: list[wavelink.abc.Playable]):
        self.songs = songs
        super().__init__(timeout = 300, disable_on_timeout = True)

    @discord.ui.button(label = "Select first", style = discord.ButtonStyle.blurple, emoji = "1️⃣")
    async def first_song(self, button: discord.Button, interaction: discord.Interaction):
        song = self.songs[0]
        self.disable_all_items()
        button.style = discord.ButtonStyle.green
        await self.message.edit(view = self)
        await interaction.response.send_message(
            embed = await play_or_queue(song = song, interaction = interaction), delete_after = 5
        )
        self.stop()

    @discord.ui.button(label = "Select second", style = discord.ButtonStyle.blurple, emoji = "2️⃣")
    async def second_song(self, button: discord.Button, interaction: discord.Interaction):
        song = self.songs[1]
        self.disable_all_items()
        button.style = discord.ButtonStyle.green
        await self.message.edit(view = self)
        await interaction.response.send_message(
            embed = await play_or_queue(song = song, interaction = interaction), delete_after = 5
        )
        self.stop()

    @discord.ui.button(label = "Select third", style = discord.ButtonStyle.blurple, emoji = "3️⃣")
    async def third_song(self, button: discord.Button, interaction: discord.Interaction):
        song = self.songs[2]
        self.disable_all_items()
        button.style = discord.ButtonStyle.green
        await self.message.edit(view = self)
        await interaction.response.send_message(
            embed = await play_or_queue(song = song, interaction = interaction), delete_after = 5
        )
        self.stop()

    @discord.ui.button(label = "Select fourth", style = discord.ButtonStyle.blurple, emoji = "4️⃣")
    async def fourth_song(self, button: discord.Button, interaction: discord.Interaction):
        song = self.songs[3]
        self.disable_all_items()
        button.style = discord.ButtonStyle.green
        await self.message.edit(view = self)
        await interaction.response.send_message(
            embed = await play_or_queue(song = song, interaction = interaction), delete_after = 5
        )
        self.stop()

    @discord.ui.button(label = "Select fifth", style = discord.ButtonStyle.blurple, emoji = "5️⃣")
    async def fifth_song(self, button: discord.Button, interaction: discord.Interaction):
        song = self.songs[4]
        self.disable_all_items()
        button.style = discord.ButtonStyle.green
        await self.message.edit(view = self)
        await interaction.response.send_message(
            embed = await play_or_queue(song = song, interaction = interaction), delete_after = 5
        )
        self.stop()


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 300)

    "⏭"
    @discord.ui.button(emoji = "⏮", custom_id = "music:prev:Track:1337")
    async def prev_track(self, button: discord.Button, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect(cls = wavelink.Player)
        vc.queue.put_at_front(vc.queue.history[1:])

    async def on_timeout(self) -> None:
        await self.message.delete()


class Music(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.players = []
        self.update_panel.start()
        log.debug("Started Music Cog")

    @tasks.loop(seconds = 20)
    async def update_panel(self):
        for player in self.players:
            await edit_panel(vc = player)

    @update_panel.before_loop
    async def before_panel_update(self):
        await self.client.wait_until_ready()

    @commands.Cog.listener("on_wavelink_track_start")
    async def on_track_start(self, player: wavelink.Player, track: wavelink.Track):
        await edit_panel(song = track, vc = player)
        if player.guild.id not in self.players:
            self.players.append(player)

    @commands.Cog.listener("on_wavelink_track_end")
    async def on_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        try:
            next_track = player.queue.get()
            await player.play(next_track)
        except wavelink.QueueEmpty:
            pass

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if not message.channel.id == 1067457865746485288:
            return
        if message.author.bot:
            return
        vc = message.guild.voice_client  # define our voice client

        if not vc:  # check if the bot is not in a voice channel
            try:
                vc = await message.author.voice.channel.connect(cls = wavelink.Player)  # connect to the voice channel
            except AttributeError:
                await message.channel.send("You are not connected to any voice channel")
        if message.author.voice.channel.id != vc.channel.id:  # check if the bot is not in the voice channel
            return await message.channel.send("You must be in the same voice channel as the bot.")

        search = message.content.strip("<>")
        if search.startswith("https://open.spotify.com/track"):
            tracks = await spotify.SpotifyTrack.search(search)
        elif search.startswith("https://open.spotify.com/playlist"):
            async for partial in spotify.SpotifyTrack.iterator(query = search):
                await play_or_queue(song = partial, interaction = message)
            music_selection = discord.Embed(
                title = f"Loaded playlist",
                color = discord.Color.blurple(),
            )
            await message.channel.send(embed = music_selection, delete_after = 10)
            await message.delete()
            return
        elif search.startswith("https://www.youtube.com/playlist") or re.match(r"^(https|http)://(?:www\.)?youtube\.com/watch\?(v=.*&list=.*)", search):
            playlist = await wavelink.YouTubePlaylist.search(search)
            for track in playlist.tracks:
                await play_or_queue(song = track, interaction = message)
            music_selection = discord.Embed(
                title = f"Loaded playlist \"{playlist.title}\"",
                color = discord.Color.blurple(),
            )
            await message.channel.send(embed = music_selection, delete_after = 10)
            await message.delete()
            return
        elif search.startswith("https://soundcloud.com"):
            tracks = await wavelink.SoundCloudTrack.search(search)
        else:
            tracks = await wavelink.YouTubeTrack.search(search)

        await message.delete()
        music_selection = discord.Embed(
            title = "Select your title",
            description = (
                "\n".join(
                    f"**{i + 1}.** [{t.title}]({t.uri})\n-> {t.author}\n-> {utility.sec_to_min(t.length)}"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            color = discord.Color.blurple(),
        )
        music_selection.set_author(name = "Query Results")
        await message.channel.send(embed = music_selection, view = SelectSongView(songs = tracks), delete_after = 20)

    @commands.command(name = "music_panel", description = "Summons the music panel")
    async def panel(self, ctx: commands.Context):
        msg = await ctx.send("this will be the music dashboard!")
        await db.insert_settings(setting_name = "panel_msg", setting = msg.id, guild = ctx.guild.id)
        await db.insert_settings(setting_name = "panel_channel", setting = ctx.channel.id, guild = ctx.guild.id)

    @commands.slash_command(name = "test_songs", description = "testing")
    async def test_songs(self, ctx: discord.ApplicationContext):
        track0 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=s47NEW6uQr8", return_first = True)
        track1 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=Hrph2EW9VjY", return_first = True)
        track2 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=tywkWRsjGbY", return_first = True)
        track3 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=nGc0BAZIcLE", return_first = True)
        track4 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=qeMFqkcPYcg", return_first = True)
        track5 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=3s_Sj4Rtah8", return_first = True)
        track6 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=cvvd-9azD1M", return_first = True)
        track7 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=JRfuAukYTKg", return_first = True)
        track8 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=HyHNuVaZJ-k", return_first = True)
        track9 = await wavelink.YouTubeTrack.search("https://www.youtube.com/watch?v=W9P_qUnMaFg", return_first = True)
        await play_or_queue(song = track0, interaction = ctx.interaction)
        await play_or_queue(song = track1, interaction = ctx.interaction)
        await play_or_queue(song = track2, interaction = ctx.interaction)
        await play_or_queue(song = track3, interaction = ctx.interaction)
        await play_or_queue(song = track4, interaction = ctx.interaction)
        await play_or_queue(song = track5, interaction = ctx.interaction)
        await play_or_queue(song = track6, interaction = ctx.interaction)
        await play_or_queue(song = track7, interaction = ctx.interaction)
        await play_or_queue(song = track8, interaction = ctx.interaction)
        await play_or_queue(song = track9, interaction = ctx.interaction)


def setup(bot):
    bot.add_cog(Music(bot))
