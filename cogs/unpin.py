import discord
from discord.ext.commands import Cog
from os import path, makedirs
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
	"""Reply to unpinned messages in the channel they were posted."""

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Unpin cog")

	@Cog.listener()
	async def on_guild_channel_pins_update(self, channel: discord.TextChannel | discord.Thread, last_pin):
		logger.info(f"unpin detected")

		guild = channel.guild

		entry = await guild.audit_logs(limit=1,action=discord.AuditLogAction.message_unpin).flatten()
		message_id = entry[0].extra.message_id
		message = await channel.fetch_message(message_id)
		url = f"https://discord.com/channels/{guild.id}/{channel.id}/{message.id}"

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