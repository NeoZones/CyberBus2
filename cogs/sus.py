import discord
from discord.ext.commands import Cog
import re

def setup(bot):
	bot.add_cog(Sus(bot))

class Sus(Cog):
	"""Obviate the need for ByteMoth"""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Sus cog")

	@Cog.listener()
	async def on_message(self, message):
		if message.author.id == self.bot.user.id:
			return
		r = re.compile(
			r'''
			\bsus\b
			|\bsussy\b
			|\bamong\sus\b
			|\bamongus
			|\bamogus
			|\bimpostor(?!.*syndrome)
			|\bimposter(?!.*syndrome)
			''',
			re.VERBOSE | re.IGNORECASE
			)
		if r.findall(message.content):
			await message.add_reaction(self.bot.get_emoji(844243428577116201))