import discord
from discord.ext import commands

def setup(bot):
	bot.add_cog(Sus(bot))

import re
class Sus(commands.Cog):
	"""Obviate the need for ByteMoth"""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Sus cog")

	@commands.Cog.listener()
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
			''',
			re.VERBOSE | re.IGNORECASE
			)
		if r.findall(message.content):
			await message.add_reaction(self.bot.get_emoji(844243428577116201))