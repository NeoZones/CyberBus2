import discord
from discord.ext.commands import Cog, command
from discord.ext.pages import Paginator
import asyncio # used to run async functions within regular functions
import subprocess # for running ffprobe and getting duration of files
from os import getenv # unused - can fetch user/pass for age-restricted videos
from time import time # performance tracking
import random # for shuffling the queue
import math # for ceiling function in queue pages
from functools import partial

def setup(bot):
	bot.add_cog(Music(bot))

def format_time(d):
	h = d // 3600
	m = d % 3600 // 60
	s = d % 60
	if h:
		return '{}:{:02}:{:02}'.format(h,m,s)
	return '{}:{:02}'.format(m,s)

def format_date(d):
	return f"{d[:4]}/{d[4:6]}/{d[6:]}"

class Player(discord.PCMVolumeTransformer):

	def __init__(self,
		source,
		duration,
		*,
		data = None,
	):
		super().__init__(discord.FFmpegPCMAudio(source, **ffmpeg_options))
		self.packets_read = 0
		self.source = source
		self.duration = duration
		self.data = data
	
	@classmethod
	async def prepare_file(cls, track, *, loop):
		loop = loop or asyncio.get_event_loop()
		return cls(track.source, track.duration, data = data)

	@classmethod
	async def prepare_stream(cls, track, *, loop):
		loop = loop or asyncio.get_event_loop()
		to_run = partial(ytdl.extract_info, url = track.source, download = False)
		data = await loop.run_in_executor(None, to_run)
		return cls(data['url'], track.duration, data = data)


	def __repr__(self):
		return ''.join([f"{key=}\n" for key in self.__dict__])

	def __str__(self):
		return (
			f"{self.original}\n"
			f"{self.progress}"
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
		elapsed = format_time(int(self.elapsed))
		duration = format_time(int(self.duration)) if self.duration else "?:??"
		return f"{elapsed} / {duration}"
	
	@property
	def length(self) -> str:
		return format_time(int(self.duration))

class Track:

	def __init__(
		self,
		*,
		source: str,
		requester: discord.User,
		title: str = None,
		duration = None,
		author: str = None,
		author_icon: str = None,
		data = None,
	):
		self.source = source
		self.requester = requester
		self.title = title
		self.duration = duration
		self.author = author
		self.data = data
	
	def __repr__(self):
		return ''.join([f"{key=}\n" for key in self.__dict__])
	
	def __str__(self):
		title = f"**{self.title}**" if self.title else f"`{self.source}`"
		duration = f" ({format_time(int(self.duration))})" if self.duration else " (?:??)"
		return title + duration + f"\nRequested by {self.requester.display_name} ({self.requester})"

class Music(Cog):
	"""Play audio within a voice channel."""
	
	REPEAT_NONE = 0
	REPEAT_ONE = 1
	REPEAT_ALL = 2

	MAX_RESULTS = 5
	PAGE_SIZE = 10

	def __init__(self, bot):
		self.bot = bot
		self.q = []
		self.track = None
		self.repeat_mode = Music.REPEAT_NONE
		self.search_results = None
		self.i = -1
		print("Initialized Music cog")
	
	@command(aliases=['start', 'summon', 'connect'])
	async def join(self, ctx, *, channel: discord.VoiceChannel = None):
		"""Joins a voice channel"""
		if not channel: # Upon a raw "join" command without a channel specified,
			if not ctx.author.voice:
				return await ctx.send(
					"You must either be in a voice channel, "
					"or specify a voice channel in order to use this command"
					)
			channel = ctx.author.voice.channel # bind to your current vc channel.
		if ctx.voice_client: # If the bot is in a different channel,
			return await ctx.voice_client.move_to(channel) # move to your channel.
		await channel.connect() # Finally, join the chosen channel.
	
	@command(aliases=['quit', 'dismiss', 'disconnect'])
	async def leave(self, ctx):
		"""Stop+disconnect from voice"""
		if ctx.voice_client:
			await ctx.voice_client.disconnect()
	
	def get_duration_from_file(self, filename):
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
		# Detect if the track should be downloaded
		download = False
		if query.endswith('!dl'):
			download = True
			query = query[:-3]
		elif query.endswith('!download'):
			download = True
			query = query[:-9]
		# Handle attachment playback
		if query == "file":
			return await self.get_tracks_from_attachments(ctx)
		# Handle online playback
		elif query.startswith('http'):
			return await self.get_tracks_from_url(ctx, query, download=download)
		# Handle local playback
		elif tracks := await self.get_tracks_from_path(ctx, query):
			return tracks
		# Do a youtube search if not found and no prior search
		elif not self.search_results:
			return await self.search_youtube(ctx, query=query)
		# Handle prior search
		try:
			i = int(query) - 1
		except ValueError:
			return ctx.send(f"Please provide an integer between 1 and {self.MAX_RESULTS}")
		if i not in range(self.MAX_RESULTS + 1):
			return ctx.send(f"Please provide an integer between 1 and {self.MAX_RESULTS}")
		url = f"https://youtube.com{self.search_results[i]['url_suffix']}"
		self.search_results = []
		return await self.get_tracks_from_url(ctx, url)
	
	async def get_tracks_from_url(self, ctx, url, download=False):
		try:
			data = ytdl.extract_info(url, download=download)
			# Detect tabs
			if data['extractor'] == 'youtube:tab' and not "entries" in data:
				data = ytdl.extract_info(data['url'], download=download) # process the playlist url
		except Exception as e:
			return e
		# Detect playlists
		entries = [data] # Assume that there is only one song.
		if "entries" in data: # If we're wrong, just overwrite our singlet list.
			entries = data["entries"] # yapf: disable
		# Create Track objects
		tracks = []
		for entry in entries:
			url = entry["url"]
			title = entry["title"]
			duration = None
			data = entry
			if not "duration" in entry and not "duration_string" in data:
				start = time()
				data = ytdl.extract_info(url, download=download)
				print(f"Refetching data took {time() - start} seconds")
			if "duration" in entry:
				duration = data["duration"]
			elif "duration_string" in entry:
				d = [int(x) for x in data["duration_string"].split(':')]
				if len(d) == 2:
					m,s = d
					h = 0
				elif len(d) == 3:
					h,m,s = d
				duration = s + 60*m + 3600*h
			tracks.append(
				Track(
					source=url,
					requester=ctx.message.author,
					title=title,
					duration=duration,
					data=data
				)
			)
		return tracks
	
	async def get_tracks_from_path(self, ctx, query):
		"""Attempt to load a local file from path"""
		if "/.." in query:
			return None
		filename = f"sounds/normalized/{query}"
		try:
			player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename))
		except:
			return None
		if player.read():
			return [
				Track(
					source=filename,
					requester=ctx.message.author,
					title=query,
					duration=self.get_duration_from_file(filename)
				)
			]
		return None
	
	async def get_tracks_from_attachments(self, ctx):
		"""Fetch the attachment URL and convert it to a track"""
		attachments = ctx.message.attachments
		tracks = []
		for attachment in attachments:
			try:
				track = await self.get_tracks_from_url(ctx, attachment.url, download=False)
				tracks += track
			except Exception as e:
				await ctx.send(
				f"An error occurred while adding `{attachment.filename}`:\n"
				f"```{e.exc_info[1]}```"
				)
		return tracks

	@command(name='search')
	async def search_youtube(self, ctx, *, query):
		"""Do a YouTube search for the given query"""
		try:
			self.search_results = ytdl.extract_info(f"ytsearch{self.MAX_RESULTS}:{query}", download=False)
		except Exception as e:
			await ctx.send(
			f"An error occurred while searching for `{query}`:\n"
			f"```{e.exc_info[1]}```"
			)
		await self.results(ctx)
	
	@command()
	async def results(self, ctx):
		"""Show results of a prior search"""
		if not self.search_results:
			return await ctx.send("There are no stored search results right now.")

		embeds = []

		formatted_results = (
		f"Performed a search for `{self.search_results['id']}`.\n"
		"Which track would you like to play?\n"
		"Make your choice using the `play` command.\n\n"
		)

		for i, result in enumerate(self.search_results['entries']):

			if result['live_status'] == "is_upcoming":
				continue # skip YT Premieres

			title = result['title']
			duration = format_time(int(result['duration']))
			uploader = result['uploader']
			views = "{:,}".format(result['view_count'])
			image = result['thumbnails'][-1]['url']
			height = result['thumbnails'][-1]['height']
			width = result['thumbnails'][-1]['width']
			url = result['url']

			formatted_results += (
			f"{i+1}: **{title}** ({duration})\n"
			f"{uploader} - {views} views\n"
			)

			embeds.append(
				discord.Embed(
					title = title,
					url = url,
					type = 'image',
					colour = 0xff0000,
				).add_field(
					name = "Duration",
					value = duration,
				).add_field(
					name = "Views",
					value = views,
				).add_field(
					name = "Uploaded by",
					value = uploader,
				).set_thumbnail(
					url = image,
				)
			)

		return await ctx.send(formatted_results, embeds = embeds)

	async def play_next(self, ctx):
		if not ctx.voice_client:
			return

		if self.repeat_mode == Music.REPEAT_NONE:
			self.track = self.q.pop(0)
		elif self.repeat_mode == Music.REPEAT_ONE:
			self.track = self.track
		elif self.repeat_mode == Music.REPEAT_ALL:
			self.i += 1
			if self.i >= len(self.q):
				self.i = 0
			self.track = self.q[self.i]

		if self.track.source.startswith('http'):
			player = await Player.prepare_stream(self.track, loop = self.bot.loop)
		else:
			player = await Player.prepare_file(self.track, loop = self.bot.loop)
		
		ctx.voice_client.play(
			player,
			after=lambda e: self.after(ctx)
		)
	
	def after(self, ctx):
		if not self.q:
			asyncio.run_coroutine_threadsafe(
				ctx.send(f"Finished playing queue."),
				self.bot.loop
			).result()
		if self.q and not ctx.voice_client.is_playing():
			asyncio.run_coroutine_threadsafe(
				self.play_next(ctx),
				self.bot.loop
			).result()

	def check_for_numbers(self, ctx):
		"""anti numbers action"""
		NUMBERS = 187024083471302656
		RICKY = 949503750651936828
		if ctx.author.id != NUMBERS:
			return True
		# if ctx.author.voice:
		# 	members = ctx.author.voice.channel.members
		# 	current_vc_members = {member.id for member in members}
		# 	other_members = current_vc_members - {NUMBERS} - {RICKY}
		# 	return (NUMBERS in current_vc_members) and not other_members
		return True

	async def add_to_queue(self,
		ctx,
		query: str,
		top: bool = False
	):
		# Check for permission to add tracks
		allowed = self.check_for_numbers(ctx)
		if not allowed:
			return await ctx.send(
			"You must be in a voice chat by yourself "
			"in order to use this command."
			)
		# Ensure we are connected to voice
		if not ctx.voice_client:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				return await ctx.send(
				"You are not connected to a voice channel. "
				"Use the `join` command with a specified channel "
				"or while connected to a channel before trying to "
				"play any tracks."
				)
		# Guard against errors
		tracks = await self.get_tracks_from_query(ctx, query)
		if isinstance(tracks, Exception):
			return await ctx.send(
			f"An error occurred while trying to add `{query}` to the queue:\n"
			f"```{tracks}```"
			)
		if not tracks: # a search was performed instead
			return
		# Add track(s) to queue
		if top:
			self.q = tracks + self.q
		else:
			self.q = self.q + tracks
		if ctx.voice_client.is_playing():
			if top:
				return await ctx.send(f"Added **{len(tracks)}** track(s) to top of queue.")
			else:
				return await ctx.send(f"Added **{len(tracks)}** track(s) to queue.")
		# If not playing, start playing
		if len(self.q) == 1:
			await ctx.send(f"Playing **{self.q[0].title}**") 
		else:
			await ctx.send(f"Playing {len(tracks)} tracks.")
		await self.play_next(ctx)


	@command(aliases=['p', 'listen'])
	async def play(self, ctx, *, query):
		"""Add track(s) to queue"""
		return await self.add_to_queue(ctx, query, top=False)

	@command(aliases=['ptop', 'top'])
	async def playtop(self, ctx, *, query):
		"""Add tracks to top of queue"""
		return await self.add_to_queue(ctx, query, top=True)
	
	# TODO: repeat once, repeat all, repeat none (repeat/loop command)
	# TODO: move positions of songs?
	# TODO: cleanup command for clearing songs requested by users not in vc?
	# TODO: remove duplicates?
	# TODO: remove range of songs
	# TODO: restart current song
	# TODO: seek command? [no fuckin idea how]
	# TODO: skip multiple songs?
	# TODO: autoplay???? [???????????]
	# TODO: filters? bass boost? nightcore? speed? [probs not]
	
	@command(aliases=['q'])
	async def queue(self, ctx, p: int = 1):
		"""Show tracks up next"""
		if not self.q and not self.track:
			return await ctx.send("The queue is currently empty.")
		full_q = [self.track] + self.q
		page = full_q[self.PAGE_SIZE*(p-1):self.PAGE_SIZE*p]
		formatted_results = ""
		formatted_results += f"Page {p} of {math.ceil(len(full_q) / self.PAGE_SIZE)}:\n"
		for i, track in enumerate(page):
			if i == 0:
				formatted_results += "=== Currently playing ===\n"
			formatted_results += (
				f"{(p-1)*self.PAGE_SIZE+i+1}: {track}\n"
			)
			if i == 0:
				formatted_results += "=== Up next ===\n"
		await ctx.send(formatted_results)
	
	@command(aliases=['np'])
	async def nowplaying(self, ctx):
		"""Show currently playing track"""
		if not self.track:
			return await ctx.send("Nothing is currently playing")
		source = ctx.voice_client.source
		embed = discord.Embed(
				title=f"{self.track.title}",
			).add_field(
				name="Progress",
				value=f"{source.progress}",
			).set_footer(
				text=f"Requested by {self.track.requester.display_name} ({self.track.requester})",
				icon_url=f"{self.track.requester.display_avatar.url}",
			)
		if "thumbnail" in source.data:
			thumb = source.data['thumbnail']
		elif "thumbnails" in source.data:
			thumb = source.data['thumbnails'][0]['url']
		embed.set_thumbnail(
			url=thumb
		)
		await ctx.send(
			f"Now playing:\n{self.track}",
			embed = embed
		)
	
	@command()
	async def skip(self, ctx):
		"""Start playing next track"""
		if ctx.voice_client.is_playing():
			if self.track:
				await ctx.send(f"Skipping: {self.track.title}")
			ctx.voice_client.stop()
	
	@command()
	async def remove(self, ctx, i):
		"""Remove track at given position"""
		i = int(i) - 1
		track = self.q.pop(i)
		await ctx.send(f"Removing: {track.title}")
	
	@command()
	async def pause(self, ctx):
		"""Pause the currently playing track"""
		if ctx.voice_client.is_playing():
			ctx.voice_client.pause()
			await ctx.send(f"Playback is paused.")
	
	@command()
	async def resume(self, ctx):
		"""Resume playback of a paused track"""
		if ctx.voice_client.is_paused():
			ctx.voice_client.resume()
			await ctx.send(f"Playback is resuming.")
	
	@command()
	async def shuffle(self, ctx):
		if not self.q:
			return await ctx.send("There is no queue to shuffle")
		self.q = random.shuffle(self.q)
		await ctx.send("Queue has been shuffled")

	@command()
	async def stop(self, ctx):
		"""Clear queue and stop playing"""
		self.q = []
		self.track = None
		if ctx.voice_client:
			if ctx.voice_client.is_connected():
				ctx.voice_client.stop()
		await ctx.send(f"Stopped playing tracks and cleared queue.")
	
	@command()
	async def clear(self, ctx):
		"""Clear queue, but keep playing"""
		self.q = []
		await ctx.send(f"Queue has been cleared.")
		
	@command(aliases=['v', 'vol'])
	async def volume(self, ctx, volume: int):
		"""Changes the player's volume"""
		if ctx.voice_client is None:
			return await ctx.send("Not connected to a voice channel.")
		if volume not in range(101):
			return await ctx.send(f"Please use an integer from 0 to 100")
		ctx.voice_client.source.volume = volume / 100
		await ctx.send(f"Changed volume to {volume}%")
	
	@command(aliases=['list'])
	async def catalogue(self, ctx, subdirectory=""):
		"""Shows the available local files"""
		if "../" in subdirectory:
			return await ctx.send(f"Nice try, but that won't work.")
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

"""
Initialize youtube-dl service.
"""
import yt_dlp as youtube_dl
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
	# "source_address": "0.0.0.0", # Bind to ipv4 since ipv6 addresses cause issues
	"extract_flat": True, # massive speedup for fetching metadata, at the cost of no upload date
	"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}
username = getenv("YOUTUBE_USERNAME")
password = getenv("YOUTUBE_PASSWORD")
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)