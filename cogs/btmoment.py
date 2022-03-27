import discord
from discord.ext.commands import Cog
from os import path, makedirs
import logging
from datetime import datetime

if not path.exists('.logs'):
	makedirs('.logs')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('.logs/btmoment.log')
formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

def setup(bot):
	bot.add_cog(BTMoment(bot))

class BTMoment(Cog):
	"""Log when a member joins VC, for pinging purposes"""

	CHANNEL = 620028244887994408

	def __init__(self, bot):
		self.bot = bot
		self.channel = self.bot.get_channel(BTMoment.CHANNEL)
		print("Initialized BTMoment cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(BTMoment.CHANNEL)

	@Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		if member.id != 257945316479729665: # ignore everyone except cass
			return
		if not after.channel: # ignore leaving -- only check for join or move
			return
		
		history = await self.channel.history(limit=2).flatten()
		m2 = history[0] # second-to-last message
		m1 = history[1] # last message
		logger.debug(f"{m2=}")
		logger.debug(f"{m1=}")

		bt_moment = False

		if ( # last 2 messages from ricky had embeds where owly left then joined
			m2.author.id == m1.author.id
			and m2.author.id == self.bot.user.id
			and m2.embeds
			and m1.embeds
			and "left" in m2.embeds[0].title
			and "joined" in m1.embeds[0].title
			and "Owly#6604" in m2.embeds[0].author.name
			and "Owly#6604" in m1.embeds[0].author.name
			and (m2.created_at - m1.created_at).total_seconds() < 120
		):
			logger.debug("BTMoment event was received after VCJoin event")
			bt_moment = True
		elif ( # last message from ricky had embed where owly left
			m1.author.id == self.bot.user.id
			and m1.embeds
			and "left" in m1.embeds[0].title
			and "Owly#6604" in m1.embeds[0].author.name
			and (datetime.now() - m1.created_at).total_seconds() < 120
		):
			logger.debug("BTMoment event was received before VCJoin event")
			bt_moment = True

		if not bt_moment:
			return

		msg = await self.channel.send("bt moment")
		if msg:
			logger.info("Message sent: bt moment")
