import discord
from discord.ext import commands

def setup(bot):
	bot.add_cog(Random(bot))

import requests
class Random(commands.Cog):
	"""Use random.org to provide a truly random result"""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Random cog")
	
	@commands.command(aliases=['dice'])
	async def roll(self, ctx, query: str = None):
		"""Roll some dice. Defaults to 1d6."""
		if not query:
			query = 'd6'
		number, faces = query.split('d')
		if not number:
			number = '1'
		number = int(number)
		faces = int(faces)
		result = requests.get(f'https://www.random.org/integers/?num={number}&min=1&max={faces}&col=1&base=10&format=plain&rnd=new').text
		await ctx.send(result)

	@commands.command(aliases=['coin'])
	async def flip(self, ctx, number: int = None):
		"""Flip a coin. Defaults to 1 flip."""
		if not number:
			number = 1
		result = requests.get(f'https://www.random.org/integers/?num={number}&min=1&max=2&col=1&base=10&format=plain&rnd=new').text
		result = result.replace('1', 'Heads')
		result = result.replace('2', 'Tails')
		await ctx.send(result)