import discord
from discord.ext.commands import Cog

def setup(bot):
	bot.add_cog(Piss(bot))

class Piss(Cog):
	"""Provide too much information when a certain substance is mentioned"""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Piss cog")

	@Cog.listener()
	async def on_message(self, message):
		if message.author.id == self.bot.user.id:
			return
		if "piss" in message.content.lower():
			await message.reply("I have kinks!", mention_author=False)
		elif "kink" in message.content.lower():
			await message.reply("I have kinks! PISS", mention_author=False)