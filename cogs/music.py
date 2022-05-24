import discord
from discord.ext.commands import Cog, command, Context
from discord.ext.pages import Paginator
import asyncio # used to run async functions within regular functions
import subprocess # for running ffprobe and getting duration of files
from os import getenv, path, makedirs
from time import time # performance tracking
import random # for shuffling the queue
import math # for ceiling function in queue pages
from functools import partial
import logging

if not path.exists('.logs'):
		makedirs('.logs')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
fh = logging.FileHandler('.logs/music.log')
formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
if not len(logger.handlers):
	logger.addHandler(fh)

def setup(bot: discord.Bot):
	bot.add_cog(Music(bot))

def format_time(d: int) -> str:
	"""Convert seconds to timestamp"""
	h = d // 3600
	m = d % 3600 // 60
	s = d % 60
	if h:
		return '{}:{:02}:{:02}'.format(h,m,s)
	return '{}:{:02}'.format(m,s)

def format_date(d: str) -> str:
	"""Convert YYYYMMDD to YYYY/MM/DD"""
	return f"{d[:4]}/{d[4:6]}/{d[6:]}"

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
		data: dict = None,
	):
		self.source = source
		self.requester = requester
		self.title = title
		self.duration = duration
		self.author = author
		self.data = data
	
	def __repr__(self):
		return f"<Track {self.source=} {self.requester=} {self.title=} {self.duration=} {self.data=}"
	
	def __str__(self):
		title = f"**{self.title}**" if self.title else f"`{self.source}`"
		duration = f" ({format_time(int(self.duration))})" if self.duration else " (?:??)"
		return (
			title + duration + f"\nRequested by {self.requester.display_name} ({self.requester})"
			if self.requester
			else
			title + duration + f"\nRequested by ???"
		)

class Player(discord.PCMVolumeTransformer):

	def __init__(self,
		source,
		duration,
		*,
		data = None,
		ffmpeg_options = {"options": "-vn"},
	):
		super().__init__(discord.FFmpegPCMAudio(source, **ffmpeg_options))
		self.packets_read = 0
		self.source = source
		self.duration = duration
		self.data = data
		logger.info(f"Player created for {source}")
	
	@classmethod
	async def prepare_file(cls, track: Track, *, loop):
		loop = loop or asyncio.get_event_loop()
		logger.info(f"Preparing player from file: {track.source}")
		return cls(track.source, track.duration, data = track.data, ffmpeg_options = {"options": "-vn"})

	@classmethod
	async def prepare_stream(cls, track: Track, *, loop):
		loop = loop or asyncio.get_event_loop()
		logger.info(f"Preparing player from stream: {track.source}")
		to_run = partial(ytdl.extract_info, url = track.source, download = False)
		data = await loop.run_in_executor(None, to_run)
		logger.info(f"Stream URL: {data['url']}")
		return cls(data['url'], track.duration, data = data, ffmpeg_options = {"options": "-vn", "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"})

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

class Music(Cog):
	"""Play audio within a voice channel."""

	REPEAT_NONE = 0
	REPEAT_ONE = 1
	REPEAT_ALL = 2

	MAX_RESULTS = 5
	PAGE_SIZE = 10

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		self.q: list[Track] = []
		self.track: Track | None = None
		self.repeat_mode = Music.REPEAT_NONE
		self.search_results: dict = None
		self.i: int = -1
		print("Initialized Music cog")
	
	@command(aliases=['start', 'summon', 'connect'])
	async def join(self, ctx: Context, *, channel: discord.VoiceChannel = None):
		"""Joins a voice channel"""
		logger.info(f".join {channel}" if channel else ".join")
		if not channel: # Upon a raw "join" command without a channel specified,
			if not ctx.author.voice:
				msg =  await ctx.send(
					"You must either be in a voice channel, "
					"or specify a voice channel in order to use this command"
					)
				if msg:
					logger.info(f"Message sent: no channel specified, and {ctx.author} is not in a voice channel")
				return
			channel = ctx.author.voice.channel # bind to your current vc channel.
		if ctx.voice_client: # If the bot is in a different channel,
			await ctx.voice_client.move_to(channel) # move to your channel.
			logger.info(f"existing voice client moved to {channel}")
			return
		voice_client = await channel.connect() # Finally, join the chosen channel.
		if voice_client:
			logger.info("voice client created")
	
	@command(aliases=['quit', 'dismiss', 'disconnect'])
	async def leave(self, ctx: Context):
		"""Stop+disconnect from voice"""
		logger.info(".leave")
		if ctx.voice_client:
			await ctx.voice_client.disconnect()
			logger.info("voice client disconnected")
	
	def get_duration_from_file(self, filename: str):
		cmd = subprocess.run(
			[
			'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
			'default=noprint_wrappers=1:nokey=1', filename
			],
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT
		)
		return float(cmd.stdout)
	
	async def get_tracks_from_query(self, ctx: Context, query: str):
		logger.debug(f"get_tracks_from_query() called for query: {query}")
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
			logger.info(f"getting tracks from attachment")
			return await self.get_tracks_from_attachments(ctx)
		# Handle online playback
		elif query.startswith('http'):
			logger.info(f"getting tracks from url")
			return await self.get_tracks_from_url(ctx, query, download=download)
		# Handle local playback
		elif tracks := await self.get_tracks_from_path(ctx, query):
			logger.info(f"getting tracks from path to local file")
			return tracks
		# Do a youtube search if not found and no prior search
		elif not self.search_results:
			logger.info(f"performing a search result")
			return await self.search_youtube(ctx, query=query)
		# Handle prior search
		try:
			i = int(query) - 1
		except ValueError:
			logger.info(f"performing a search result")
			return await self.search_youtube(ctx, query=query)
		if i not in range(self.MAX_RESULTS + 1):
			return await ctx.send(f"Please provide an integer between 1 and {self.MAX_RESULTS}")
		url = self.search_results['entries'][i]['url']
		self.search_results = []
		logger.info(f"handling a prior search")
		return await self.get_tracks_from_url(ctx, url)
	
	async def get_tracks_from_url(self, ctx: Context, url: str, download: bool = False):
		logger.debug(f"get_tracks_from_url() called for URL: {url}")
		try:
			data = ytdl.extract_info(url, download=download)
			# logger.debug(f"{data=}")
			# Detect tabs
			if data['extractor'] == 'youtube:tab' and not "entries" in data:
				logger.info("youtube:tab detected, no entries in data (so not a playlist)")
				data = ytdl.extract_info(data['url'], download=download) # process the playlist url
				logger.debug(f"{data=}")
		except Exception as e:
			logger.error("Exception thrown!")
			logger.error(f"{e=}")
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
			if not "duration" in data and not "duration_string" in data:
				logger.info("duration not found in entry's extracted data -- refetching")
				logger.debug(f"{data=}")
				start = time()
				data = ytdl.extract_info(url, download=download)
				logger.info(f"Refetching data took {time() - start} seconds")
			if "duration" in data:
				duration = data["duration"]
			elif "duration_string" in data:
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
		logger.info(f"Got {len(tracks)} track(s) from URL")
		logger.debug(f"{tracks=}")
		return tracks
	
	async def get_tracks_from_path(self, ctx: Context, query: str):
		"""Attempt to load a local file from path"""
		logger.debug(f"get_tracks_from_path() called for query: {query}")
		if "/.." in query:
			return None
		filename = f"sounds/normalized/{query}"
		try:
			player = discord.FFmpegPCMAudio(filename)
		except:
			return None
		if player.read():
			logger.info("filename is readable from path")
			return [
				Track(
					source=filename,
					requester=ctx.message.author,
					title=query,
					duration=self.get_duration_from_file(filename)
				)
			]
		return None
	
	async def get_tracks_from_attachments(self, ctx: Context):
		"""Fetch the attachment URL and convert it to a track"""
		logger.debug(f"get_tracks_from_attachment() called")
		attachments = ctx.message.attachments
		tracks = []
		for attachment in attachments:
			try:
				track = await self.get_tracks_from_url(ctx, attachment.url, download=False)
				tracks += track
			except Exception as e:
				logger.error("Exception thrown!")
				logger.error(f"{e=}")
				msg = await ctx.send(
				f"An error occurred while adding `{attachment.filename}`:\n"
				f"```{e.exc_info[1]}```"
				)
				if msg:
					logger.warning("Message sent: An error occurred while adding `{attachment.filename}`")
				return e
		logger.debug(f"{tracks=}")
		return tracks

	@command(name='search')
	async def search_youtube(self, ctx: Context, *, query: str):
		"""Do a YouTube search for the given query"""
		logger.debug(f"search_youtube() called for query: {query}")
		try:
			self.search_results = ytdl.extract_info(f"ytsearch{self.MAX_RESULTS}:{query}", download=False)
		except Exception as e:
			logger.error("Exception thrown!")
			logger.error(f"{e=}")
			msg = await ctx.send(
			f"An error occurred while searching for `{query}`:\n"
			f"```{e.exc_info[1]}```"
			)
			if msg:
				logger.warning(f"Message sent: An error occurred while searching for `{query}`")
			return e
		await self.results(ctx)
	
	@command()
	async def results(self, ctx: Context):
		"""Show results of a prior search"""
		logger.debug(f"results() called")
		if not self.search_results:
			logger.info("No stored search results")
			msg = await ctx.send("There are no stored search results right now.")
			if msg:
				logger.warning("Message sent: There are no stored search results right now.")
			return

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

		msg = await ctx.send(formatted_results, embeds = embeds)
		if msg:
			logger.info("Message sent: formatted_results")

	async def play_next(self, ctx: Context):
		logger.debug("play_next() called")
		if not ctx.voice_client:
			return

		if ctx.voice_client.is_playing():
			return

		logger.info(f"{self.track=}")

		if self.repeat_mode == Music.REPEAT_NONE:
			if not self.q:
				return await ctx.send("Finished playing queue.")
			self.track = self.q.pop(0)
			logger.info("Repeat none -- popped track from queue")
		elif self.repeat_mode == Music.REPEAT_ONE:
			self.track = self.track
			logger.info("Repeat one -- keeping track the same")
		elif self.repeat_mode == Music.REPEAT_ALL:
			self.i += 1
			if self.i >= len(self.q):
				self.i = 0
			self.track = self.q[self.i]
			logger.info("Repeat all -- advancing pointer without popping track")

		logger.info(f"{self.track=}")

		if self.track.source.startswith('http'):
			# detect private or unplayable videos here
			try:
				data = ytdl.extract_info(self.track.source, download=False)
				logger.debug(f"{data=}")
			except Exception as e:
				logger.error("Exception thrown!")
				logger.error(f"{e=}")
				await ctx.send(
					f"`{self.track.source}` is unplayable -- skipping...\n"
					f"```{e.exc_info[1]}```"
				)
				logger.warning(f"Skipping as unplayable: {self.track.source}")
				return await self.play_next(ctx)
			player = await Player.prepare_stream(self.track, loop = self.bot.loop)
		else:
			player = await Player.prepare_file(self.track, loop = self.bot.loop)
		
		logger.info("playing Player on the voice client")
		ctx.voice_client.play(
			player,
			after=lambda e: self.after(ctx)
		)
	
	def after(self, ctx: Context):
		logger.debug("after() called")

		if not ctx.voice_client:
			logger.info("no voice client -- bot was disconnected from vc?")
			self.track = None
			self.q = None
			asyncio.run_coroutine_threadsafe(
				ctx.send(f"Clearing queue after bot left VC"),
				self.bot.loop
			).result()
			logger.info("Cleared queue after bot left VC")
			return

		if not self.q and self.repeat_mode == Music.REPEAT_NONE:
			logger.info("queue empty and not repeating")
			self.track = None
			asyncio.run_coroutine_threadsafe(
				ctx.send(f"Finished playing queue."),
				self.bot.loop
			).result()
			logger.info("Finished playing queue.")
			return

		if self.q and ctx.voice_client and not ctx.voice_client.is_playing():
			logger.info("queue exists and voice client is not playing")
			logger.debug(f"{self.q=}")
			logger.info("playing next...")
			asyncio.run_coroutine_threadsafe(
				self.play_next(ctx),
				self.bot.loop
			).result()
			return

	def check_for_numbers(self, ctx: Context):
		"""anti numbers action"""
		logger.debug("check_for_numbers() called")
		NUMBERS = 187024083471302656
		PIZZA = 320294046935547905
		RICKY = 949503750651936828
		if ctx.author.id in [
			NUMBERS,
			PIZZA,
		]:
			return False 
		#if ctx.author.id != NUMBERS:
		#	return False
		# if ctx.author.voice:
		# 	members = ctx.author.voice.channel.members
		# 	current_vc_members = {member.id for member in members}
		# 	other_members = current_vc_members - {NUMBERS} - {RICKY}
		# 	return (NUMBERS in current_vc_members) and not other_members
		return True

	async def add_to_queue(self,
		ctx: Context,
		query: str,
		top: bool = False
	):
		logger.debug(f"add_to_queue({query}) called")
		# Check for permission to add tracks
		allowed = self.check_for_numbers(ctx)
		if not allowed:
			logger.info(f"{ctx.author} is not allowed to add to queue")
			#return await ctx.send(
			#"You must be in a voice chat by yourself "
			#"in order to use this command."
			#)
			return await ctx.send("No 💜")
		# Ensure we are connected to voice
		if not ctx.voice_client:
			logger.warning("no voice client")
			if ctx.author.voice:
				logger.info(f"moving voice client to {ctx.author.voice.channel}")
				await ctx.author.voice.channel.connect()
			else:
				msg = await ctx.send(
				"You are not connected to a voice channel. "
				"Use the `join` command with a specified channel "
				"or while connected to a channel before trying to "
				"play any tracks."
				)
				if msg:
					logger.info("Message sent: author not in voice, and no voice client exists")
				return
		# Guard against errors
		tracks = await self.get_tracks_from_query(ctx, query)
		if isinstance(tracks, Exception):
			msg = await ctx.send(
			f"An error occurred while trying to add `{query}` to the queue:\n"
			f"```{tracks}```"
			)
			if msg:
				logger.warning(f"Message sent: An error occurred while trying to add `{query}` to the queue")
			return
		if not tracks: # a search was performed instead
			return
		# Add track(s) to queue
		if top:
			self.q = tracks + self.q
		else:
			self.q = self.q + tracks
		if ctx.voice_client.is_playing():
			if top:
				msg = await ctx.send(f"Added **{len(tracks)}** track(s) to top of queue.")
				if msg:
					logger.info(f"Message sent: Added **{len(tracks)}** track(s) to top of queue.")
				return
			else:
				msg = await ctx.send(f"Added **{len(tracks)}** track(s) to queue.")
				if msg:
					logger.info(f"Message sent: Added **{len(tracks)}** track(s) to queue.")
				return
		# If not playing, start playing
		if len(self.q) == 1:
			msg = await ctx.send(f"Playing **{self.q[0].title}**")
			if msg:
				logger.info(f"Message sent: Playing **{self.q[0].title}**")
		else:
			msg = await ctx.send(f"Playing {len(tracks)} tracks.")
			if msg:
				logger.info(f"Message sent: Playing {len(tracks)} tracks.")
		await self.play_next(ctx)

	@command(aliases=['p', 'listen'])
	async def play(self, ctx: Context, *, query: str):
		"""Add track(s) to queue"""
		if not query:
			msg = await ctx.send("No query detected")
			if msg:
				logger.info("Empty .play command was issued")
			return
		logger.info(f".play {query}")
		return await self.add_to_queue(ctx, query, top=False)

	@command(aliases=['ptop', 'top'])
	async def playtop(self, ctx: Context, *, query: str):
		"""Add tracks to top of queue"""
		if not query:
			msg = await ctx.send("No query detected")
			if msg:
				logger.info("Empty .playtop command was issued")
			return
		logger.info(f".playtop {query}")
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
	async def queue(self, ctx: Context, p: int = 1):
		"""Show tracks up next"""
		logger.info(f".queue {p}" if p else ".queue")
		# check that there is a queue and a current track
		if not self.q and not self.track:
			msg = await ctx.send("The queue is currently empty.")
			logger.info("Message sent: The queue is currently empty.")
			return
		# paginate the queue to just one page
		full_queue = [self.track] + self.q
		start = self.PAGE_SIZE * (p-1)
		end = self.PAGE_SIZE * p
		queue_page = full_queue[start:end]
		# construct header
		formatted_results = f"{len(self.q)} tracks on queue.\n"
		total_pages = math.ceil(len(full_queue) / self.PAGE_SIZE)
		formatted_results += f"Page {p} of {total_pages}:\n"
		# construct page
		for i, track in enumerate(queue_page):
			if p == 1 and i == 0: # print nowplaying on first queue page
				formatted_results += "=== Currently playing ===\n"
			formatted_results += (
				f"{start+i+1}: {track}\n"
			)
			if p == 1 and i == 0: # add separator on first page for actually queued tracks
				formatted_results += "=== Up next ===\n"
		# send text to channel
		msg = await ctx.send(formatted_results)
		if msg:
			logger.info("Message sent: Sent queue page to channel")
	
	@command(aliases=['np'])
	async def nowplaying(self, ctx: Context):
		"""Show currently playing track"""
		logger.info(".nowplaying")
		if not self.track:
			msg = await ctx.send("Nothing is currently playing")
			if msg:
				logger.info("Nothing is currently playing")
			return
		if not ctx.voice_client:
			msg = await ctx.send("Bot is not currently connected to a voice channel")
			if msg:
				logger.info("Bot not connected to VC")
			return
		source: Player = ctx.voice_client.source
		embed = discord.Embed(
				title=f"{self.track.title}",
				url=f"{self.track.source}",
			).add_field(
				name="Progress",
				value=f"{source.progress}",
			).set_footer(
				text=f"Requested by {self.track.requester.display_name} ({self.track.requester})",
				icon_url=f"{self.track.requester.display_avatar.url}",
			)
		thumb = None
		if "thumbnail" in source.data:
			thumb = source.data['thumbnail']
		elif "thumbnails" in source.data:
			thumb = source.data['thumbnails'][0]['url']
		if thumb:
			embed.set_thumbnail(
				url=thumb
			)
		msg = await ctx.send(
			f"Now playing:\n{self.track}",
			embed = embed
		)
		if msg:
			logger.info(f"Message sent: Now playing: {self.track.title}")
	
	@command()
	async def skip(self, ctx: Context):
		"""Start playing next track"""
		logger.info(".skip")
		if ctx.voice_client.is_playing():
			if self.track:
				msg = await ctx.send(f"Skipping: {self.track.title}")
				if msg:
					logger.info(f"Message sent: Skipping: {self.track.title}")
			ctx.voice_client.stop()
	
	@command()
	async def remove(self, ctx: Context, i: int):
		"""Remove track at given position"""
		logger.info(f".remove {i}")
		i -= 1 # convert to zero-indexing
		track = self.q.pop(i)
		msg = await ctx.send(f"Removed: {track.title}")
		if msg:
			logger.info(f"Message sent: Removed: {track.title}")
	
	@command()
	async def pause(self, ctx: Context):
		"""Pause the currently playing track"""
		logger.info(".pause")
		if ctx.voice_client.is_playing():
			ctx.voice_client.pause()
			msg = await ctx.send("Playback is paused.")
			if msg:
				logger.info("Message sent: Playback is paused.")
	
	@command()
	async def resume(self, ctx: Context):
		"""Resume playback of a paused track"""
		logger.info(".resume")
		if ctx.voice_client.is_paused():
			ctx.voice_client.resume()
			msg = await ctx.send("Playback is resumed.")
			if msg:
				logger.info("Message sent: Playback is resumed.")
	
	@command()
	async def shuffle(self, ctx: Context):
		"""Randomizes the current queue"""
		logger.info(".shuffle")
		if not self.q:
			return await ctx.send("There is no queue to shuffle")

		logger.debug(f"{self.track=}")
		logger.debug(f"{self.q=}")

		random.shuffle(self.q)

		logger.debug(f"{self.track=}")
		logger.debug(f"{self.q=}")
		msg = await ctx.send("Queue has been shuffled")
		if msg:
			logger.info("Message sent: Queue has been shuffled")

	@command()
	async def stop(self, ctx: Context):
		"""Clear queue and stop playing"""
		logger.info(".stop")
		self.q = []
		self.track = None
		if ctx.voice_client:
			if ctx.voice_client.is_connected():
				ctx.voice_client.stop()
		msg = await ctx.send("Stopped playing tracks and cleared queue.")
		if msg:
			logger.info("Message sent: Stopped playing tracks and cleared queue.")

	@command()
	async def clear(self, ctx: Context):
		"""Clear queue, but keep playing"""
		logger.info(".clear")
		self.q = []
		msg = await ctx.send("Queue has been cleared.")
		if msg:
			logger.info("Message sent: Queue has been cleared.")
		
	@command(aliases=['v', 'vol'])
	async def volume(self, ctx: Context, volume: int):
		"""Changes the player's volume"""
		logger.info(f".volume {volume}")
		if ctx.voice_client is None:
			return await ctx.send("Not connected to a voice channel.")
		if volume not in range(101):
			return await ctx.send(f"Please use an integer from 0 to 100")
		ctx.voice_client.source.volume = volume / 100
		await ctx.send(f"Changed volume to {volume}%")
	
	@command(aliases=['list'])
	async def catalogue(self, ctx: Context, subdirectory: str = ""):
		"""Shows the available local files"""
		logger.info(f".catalogue {subdirectory}" if subdirectory else ".catalogue")
		if "../" in subdirectory:
			return await ctx.send(f"Nice try, but that won't work.")
		path = "."
		if subdirectory:
			path += f"/{subdirectory}"
		cmd = subprocess.run(
			f"cd sounds/normalized && find {path} -type f | sort",
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
}
username = getenv("YOUTUBE_USERNAME")
password = getenv("YOUTUBE_PASSWORD")
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)