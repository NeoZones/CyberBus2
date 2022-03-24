import discord
from discord.ext.commands import Cog
from os import getenv, path
import pickle
import asyncio

def setup(bot):
	bot.add_cog(Unpin(bot))

class Unpin(Cog):
	"""Reply to unpinned messages in the channel they were posted"""

	def __init__(self, bot):
		self.bot = bot
		self.guild = bot.get_guild(int(getenv("GUILD_ID")))
		# load cache from pickle if it exists
		filename = '.cache/messages/pins.pickle'
		self.cache = set()
		if path.getsize(filename) > 0:
			with open(filename, 'r+b') as f:
				self.cache = pickle.load(f)
		else:
			# get pinned message IDs
			channels = asyncio.run_coroutine_threadsafe(
				self.guild.fetch_channels(),
				self.bot.loop or asyncio.get_event_loop()
			).result()
			channels = [channel for channel in channels if channel.type == discord.ChannelType.text]
			for channel in channels:
				try:
					pins = asyncio.run_coroutine_threadsafe(
						channel.pins(),
						self.bot.loop or asyncio.get_event_loop()
					).result()
				except:
					continue
				for message in pins:
					if message.id not in self.cache:
						self.cache.add(message.id)
			# commit cacheset to file storage
			with open(filename, 'w+b') as f:
				pickle.dump(self.cache, f)
		print("Initialized Unpin cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.guild = self.bot.get_guild(int(getenv("GUILD_ID")))
		# load cache from pickle if it exists
		filename = '.cache/messages/pins.pickle'
		self.cache = set()
		if path.getsize(filename) > 0:
			with open(filename, 'r+b') as f:
				self.cache = pickle.load(f)
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
					if message.id not in self.cache:
						self.cache.add(message.id)
			# commit cacheset to file storage
			with open(filename, 'w+b') as f:
				pickle.dump(self.cache, f)

	@Cog.listener()
	async def on_raw_message_edit(self, payload):
		guild_id = payload.guild_id
		channel_id = payload.channel_id
		message_id = payload.message_id
		
		url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

		if "pinned" not in payload.data:
			return
		
		pinned_after = payload.data['pinned']
		pinned_before = message_id in self.cache
		if pinned_after and not pinned_before: # Pinned already generates a native message, so ignore pins
			self.cache.add(message_id) # but we should still cache this pin
			return
		if pinned_before and not pinned_after: # Generate a notice for unpinned messages
			channel = self.bot.get_channel(channel_id)
			message = payload.cached_message or await channel.fetch_message(message_id)
			await channel.send(
				embed = discord.Embed(
					title = "Message unpinned",
					url = url
				),
				reference = message,
				mention_author = False
			)