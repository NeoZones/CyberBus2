import discord
from discord.ext import commands, pages
import asyncio
import subprocess
from datetime import timedelta

def setup(bot):
	bot.add_cog(Music(bot))

MAX_RESULTS = 5
results = None
q = []
track = None

class Track:
	
	def __init__(
		self,
		source: str,
		title: str,
		duration: float,
		requester: discord.User
	):
		self.title = title
		self.duration = duration
		self.requester = requester
		self.packets_read = 0
		self.source = source
	
	def __repr__(self):
		return (
			f"{self.title=}\n"
			f"{self.duration=}\n"
			f"{self.requester=}\n"
			f"{self.packets_read=}\n"
			f"{self.source=}\n"
		)
	
	def __str__(self):
		return (
			f"**{self.title}**\n" + f"({self.progress})\n" +
			f"Requested by: {self.requester}"
		)
	
	def read(self) -> bytes:
		data = self.original.read()
		if data:
			self.packets_read += 1
		return data
	
	@property
	def elapsed(self) -> float:
		return self.packets_read * 0.02 # each packet is 20ms
	
	@property
	def progress(self) -> str:
		elapsed = str(timedelta(seconds=int(self.elapsed)))
		duration = str(timedelta(seconds=int(self.duration)))
		return f"{elapsed} / {duration}"
	
	@property
	def length(self) -> str:
		return str(timedelta(seconds=int(self.duration)))

class Music(commands.Cog):
	"""Play audio within a voice channel."""
	
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Music cog")
	
	@commands.command(aliases=['start', 'summon', 'connect'])
	async def join(self, ctx, *, channel: discord.VoiceChannel = None):
		"""Joins a voice channel"""
		if not channel: # Upon a raw "join" command without a channel specified,
			channel = ctx.author.voice.channel # bind to your current vc channel.
		if ctx.voice_client: # If the bot is in a different channel,
			return await ctx.voice_client.move_to(channel) # move to your channel.
		await channel.connect() # Finally, join the chosen channel.
	
	@commands.command(aliases=['quit', 'dismiss', 'disconnect'])
	async def leave(self, ctx):
		"""Stop+disconnect from voice"""
		await ctx.voice_client.disconnect()
	
	def get_duration(self, filename):
		cmd = subprocess.run(
			[
			'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
			'default=noprint_wrappers=1:nokey=1', filename
			],
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT
		)
		return float(cmd.stdout)
	
	async def get_tracks_from_query(self, ctx, query):
		"""Detect if the track should be downloaded"""
		download = False
		if query.endswith('!dl'):
			download = True
			query = query[:-3]
		if query.endswith('!download'):
			download = True
			query = query[:-9]
		"""Handle attachment playback"""
		if query == "file":
			return await self.get_tracks_from_attachments(ctx)
		"""Handle online playback"""
		if query.startswith('http'):
			return await self.get_tracks_from_url(ctx, query, download=download)
		"""Handle local playback"""
		if tracks := await self.get_tracks_from_path(ctx, query):
			return tracks
		"""Handle prior search"""
		global results
		global MAX_RESULTS
		if results:
			try:
				i = int(query) - 1
			except ValueError:
				return ctx.send(f"Please provide an integer between 1 and {MAX_RESULTS}")
			if i not in range(MAX_RESULTS + 1):
				return ctx.send(f"Please provide an integer between 1 and {MAX_RESULTS}")
			url = f"https://youtube.com{results[i]['url_suffix']}"
			results = []
			return await self.get_tracks_from_url(ctx, url)
		"""Do a youtube search if none found"""
		await self.search_youtube(ctx, query)
	
	async def get_tracks_from_url(self, ctx, url, download=False):
		"""Load a song or playlist from a URL"""
		loop = self.bot.loop or asyncio.get_event_loop()
		try:
			data = await loop.run_in_executor(
				None, # use the default Executor
				lambda: ytdl.extract_info(url, download=download)
			)
		except Exception as e:
			return e
		"""Detect playlists"""
		tracks = []
		entries = [data] # Assume that there is only one song.
		if "entries" in data: # If we're wrong, just overwrite our singlet list.
			entries = data["entries"] # yapf: disable
		"""Create Track objects"""
		for entry in entries:
			url = entry["url"]
			title = entry["title"]
			try:
				duration = entry["duration"]
			except:
				data = await loop.run_in_executor(
					None, # use the default Executor
					lambda: ytdl.extract_info(url, download=True)
				)
				filename = (
					f".cache/" +
					f"{data['extractor']}-{data['id']}-{data['title']}.{data['ext']}"
				)
				duration = self.get_duration(filename)
			requester = ctx.message.author
			track = Track(url, title, duration, requester)
			tracks.append(track)
		return tracks
	
	async def get_tracks_from_path(self, ctx, query):
		"""Attempt to load a local file from path"""
		if "/.." in query:
			return None
		filename = f"sounds/normalized/{query}"
		player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename))
		if player.read():
			title = query
			duration = self.get_duration(filename)
			requester = ctx.message.author
			return [Track(filename, title, duration, requester)]
		return None
	
	async def get_tracks_from_attachments(self, ctx):
		"""Fetch the attachment URL and convert it to a track"""
		attachments = ctx.message.attachments
		tracks = []
		for attachment in attachments:
			track = await self.get_tracks_from_url(ctx, attachment.url, download=False)
			tracks += track
		return tracks

	async def search_youtube(self, ctx, query):
		"""Do a YouTube search for the given string"""
		global results
		global MAX_RESULTS
		from youtube_search import YoutubeSearch
		results = YoutubeSearch(query, max_results=MAX_RESULTS).to_dict()
		await self.results(ctx, results)
	
	@commands.command()
	async def results(self, ctx, results):
		"""Show results of a prior search"""
		formatted_results = (
			"Which track would you like to play?\n"
			"Make your choice using the `play` command.\n\n"
		)
		for i, result in enumerate(results):
			formatted_results += (
				f"{i+1}: **{result['title']}** ({result['duration']})\n"
				f"{result['channel']} - {result['views']} - {result['publish_time']}\n"
				f"https://youtube.com{result['url_suffix']}\n"
			)
		return await ctx.send(formatted_results)

	def play_next(self, ctx):
		global q
		global track
		if not q:
			track = None
			asyncio.run_coroutine_threadsafe(
				ctx.send(f"Finished playing queue."), self.bot.loop
				or asyncio.get_event_loop()
			).result()
			return
		track = q.pop(0)
		if not ctx.voice_client.is_playing():
			player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track.source, **ffmpeg_options), volume=1.0)
			ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
	
	def check_for_numbers(self, ctx):
		"""anti numbers action"""
		NUMBERS = 187024083471302656
		RICKY = 949503750651936828
		members = ctx.author.voice.channel.members
		if ctx.author.id == NUMBERS:
			current_vc_members = [
				member.id
				for member in members
			]
			other_members = current_vc_members.remove(NUMBERS).remove(RICKY)
			return (NUMBERS in current_vc_members) and not other_members
		return True

	@commands.command(aliases=['p', 'listen'])
	async def play(self, ctx, *, query):
		"""Add track(s) to queue"""
		allowed = self.check_for_numbers(ctx)
		if not allowed:
			return await ctx.send(
				"You must be in a voice chat by yourself in order to use this command."
			)
		tracks = await self.get_tracks_from_query(ctx, query)
		if not tracks or isinstance(tracks, Exception):
			return await ctx.send(
				f"An error occurred while trying to add `{query}` to the queue:\n"
				f"```{tracks.exc_info[1]}```"
			)
		global q
		q += tracks
		if ctx.voice_client.is_playing():
			return await ctx.send(f"Added **{len(tracks)}** track(s) to queue.")
		else:
			if len(q) == 1:
				await ctx.send(f"Playing **{q[0].title}**")
			else:
				await ctx.send(f"Playing {len(tracks)} tracks.")
			self.play_next(ctx)
	
	@commands.command(aliases=['ptop', 'top'])
	async def playtop(self, ctx, *, query):
		"""Add tracks to top of queue"""
		allowed = self.check_for_numbers(ctx)
		if not allowed:
			return await ctx.send(
				"You must be in a voice chat by yourself in order to use this command."
			)
		tracks = await self.get_tracks_from_query(ctx, query)
		if not tracks or isinstance(tracks, Exception):
			return await ctx.send(
				f"An error occurred while trying to add `{query}` to the queue:\n"
				f"```{tracks.exc_info[1]}```"
			)
		global q
		q = tracks + q
		if ctx.voice_client.is_playing():
			return await ctx.send(f"Added **{len(tracks)}** track(s) to top of queue.")
		else:
			if len(q) == 1:
				await ctx.send(f"Playing **{q[0].title}**")
			else:
				await ctx.send(f"Playing {len(tracks)} tracks.")
			self.play_next(ctx)
	
	# TODO: repeat once, repeat all, repeat none (repeat/loop command)
	# TODO: move positions of songs?
	# TODO: cleanup command for clearing songs requested by users not in vc?
	# TODO: remove duplicates?
	# TODO: remove range of songs
	# TODO: restart current song
	# TODO: seek command? [no fuckin idea how]
	# TODO: shuffle queue? [also idk]
	# TODO: skip multiple songs?
	# TODO: autoplay???? [???????????]
	# TODO: filters? bass boost? nightcore? speed? [probs not]
	
	@commands.command(aliases=['q'])
	async def queue(self, ctx):
		"""Show tracks up next"""
		# TODO: paginate this
		formatted_results = ""
		global q
		if not q:
			formatted_results += "The queue is currently empty."
		else:
			formatted_results += "Up next:\n"
			for i, track in enumerate(q):
				formatted_results += (
					f"{i+1}: **{track.title}** ({track.length})"
					f" - requested by {track.requester}\n"
				)
		await ctx.send(formatted_results)
	
	@commands.command(aliases=['np'])
	async def nowplaying(self, ctx):
		"""Show currently playing track"""
		global track
		await ctx.send(f"Now playing:\n{track}")
	
	@commands.command()
	async def skip(self, ctx):
		global track
		if ctx.voice_client.is_playing():
			await ctx.send(f"Skipping: {track.title}")
			return await ctx.voice_client.stop()
	
	@commands.command()
	async def remove(self, ctx, i):
		global q
		i = int(i) - 1
		track = q.pop(i)
		await ctx.send(f"Removing: {track.title}")
	
	@commands.command()
	async def pause(self, ctx):
		"""Pause the currently playing track"""
		if ctx.voice_client.is_playing():
			ctx.voice_client.pause()
			return await ctx.send(f"Playback is paused.")
	
	@commands.command()
	async def resume(self, ctx):
		"""Resume playback of a paused track"""
		if ctx.voice_client.is_paused():
			ctx.voice_client.resume()
			return await ctx.send(f"Playback is resuming.")
	
	@commands.command()
	async def stop(self, ctx):
		"""Clear queue and stop playing"""
		await self.clear(ctx)
		ctx.voice_client.stop()
		return await ctx.send(f"Stopped playing tracks and cleared queue.")
	
	@commands.command()
	async def clear(self, ctx):
		"""Clear queue, but keep playing current track"""
		if ctx.voice_client.is_connected():
			global q
			q = []
			return await ctx.send(f"Queue has been cleared.")
	
	@commands.command(aliases=['v', 'vol'])
	async def volume(self, ctx, volume: int):
		"""Changes the player's volume"""
		if ctx.voice_client is None:
			return await ctx.send("Not connected to a voice channel.")
		if volume not in range(101):
			return await ctx.send(f"Please use an integer from 0 to 100")
		ctx.voice_client.source.volume = volume / 100
		await ctx.send(f"Changed volume to {volume}%")
	
	@commands.command(aliases=['list'])
	async def catalogue(self, ctx, subdirectory=""):
		"""Shows the available local files"""
		if ".." in subdirectory:
			return
		path = "."
		if subdirectory:
			path += f"/{subdirectory}"
		cmd = subprocess.run(
			f"cd sounds/normalized && find {path} -type f",
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT
		)
		results = cmd.stdout.decode('utf-8').split('\n')[:-1]
		formatted_results = "```"
		for result in results:
			formatted_results += f"{result[2:]}\n"
		formatted_results += "```"
		await ctx.send(formatted_results)


	@play.before_invoke
	@playtop.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send("You are not connected to a voice channel.")

"""
Initialize youtube-dl service.
"""
import youtube_dl
ffmpeg_options = {"options": "-vn"}
youtube_dl.utils.bug_reports_message = lambda: ""
ytdl_format_options = {
	"format": "bestaudio/best",
	"outtmpl": ".cache/%(extractor)s-%(id)s-%(title)s.%(ext)s",
	"restrictfilenames": True,
	"noplaylist": True,
	"nocheckcertificate": True,
	"ignoreerrors": False,
	"logtostderr": False,
	"quiet": True,
	"no_warnings": True,
	"default_search": "auto",
	"source_address": "0.0.0.0", # Bind to ipv4 since ipv6 addresses cause issues
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)