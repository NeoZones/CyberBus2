import discord
from discord.ext.commands import Cog
import re

def setup(bot: discord.Bot):
	bot.add_cog(Piss(bot))

class Piss(Cog):
	"""Provide too much information when a certain substance is mentioned"""
	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Piss cog")

	@Cog.listener()
	async def on_message(self, message: discord.Message):
		if message.author.id == self.bot.user.id:
			return
		piss = re.compile(
			r'''
			\bpiss\b
			''',
			re.VERBOSE | re.IGNORECASE
			)
		kink = re.compile(
			r'''
			\bkinks?\b
			''',
			re.VERBOSE | re.IGNORECASE
			)
		
		if kink.findall(message.content):
			await message.reply("I have kinks! PISS", mention_author=False)
		# elif piss.findall(message.content):
		# 	await message.reply("I have kinks!", mention_author=False)