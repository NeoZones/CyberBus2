import discord
from discord.ext.commands import Cog
from os import getenv, path, makedirs
import pickle
import asyncio
import logging

if not path.exists('.logs'):
	makedirs('.logs')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('.logs/unpin.log')
formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
if not len(logger.handlers):
	logger.addHandler(fh)

def setup(bot: discord.Bot):
	bot.add_cog(Unpin(bot))

class Unpin(Cog):
	"""Reply to unpinned messages in the channel they were posted"""

	cache = set()

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Unpin cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.guild = await self.bot.fetch_guild(int(getenv("GUILD_ID")))
		# load cache from pickle if it exists
		if not path.exists('.cache/messages'):
			logger.info("creating .cache/messages folder")
			makedirs('.cache/messages')
		filename = '.cache/messages/pins.pickle'
		if path.getsize(filename) > 0:
			with open(filename, 'r+b') as f:
				Unpin.cache = pickle.load(f)
				logger.info("loaded pins.pickle file")
		else:
			# get pinned message IDs
			channels = await self.guild.fetch_channels()
			channels = [channel for channel in channels if channel.type == discord.ChannelType.text]
			for channel in channels:
				try:
					pins = await channel.pins()
				except:
					continue
				for message in pins:
					if message.id not in Unpin.cache:
						Unpin.cache.add(message.id)
						logger.debug(f"{message.id} added to pin cache")
			# commit cacheset to file storage
			with open(filename, 'w+b') as f:
				pickle.dump(Unpin.cache, f)

	@Cog.listener()
	async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
		guild_id = payload.guild_id
		channel_id = payload.channel_id
		message_id = payload.message_id
		
		url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

		if "pinned" not in payload.data:
			return

		pinned_after = payload.data['pinned']
		pinned_before = message_id in Unpin.cache
		if pinned_after and not pinned_before: # Pinned already generates a native message, so ignore pins
			Unpin.cache.add(message_id) # but we should still cache this pin
			logger.debug(f"{message_id} added to pin cache")
			return
		if pinned_before and not pinned_after: # Generate a notice for unpinned messages
			logger.info(f"unpin detected for message {url}")
			channel = self.bot.get_channel(channel_id)
			message = payload.cached_message or await channel.fetch_message(message_id)
			msg = await channel.send(
				embed = discord.Embed(
					title = "Message unpinned",
					url = url
				),
				reference = message,
				mention_author = False
			)
			if msg:
				logger.info(f"Message unpinned: {url}")