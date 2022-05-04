import discord
from discord.ext.commands import Cog, command, Context
from discord.commands import slash_command, Option
import requests
from os import getenv
from collections import Counter
import re

GUILD = int(getenv("GUILD_ID"))

def setup(bot: discord.Bot):
	bot.add_cog(Random(bot))

class Random(Cog):
	"""Use random.org to provide truly random results"""
	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Random cog")

# ==============================================================================

	@staticmethod
	def roll(faces: int = 6, number: int = 1) -> str:
		"""Roll die(s) using random.org integer generation"""
		columns = number if number < 11 else 10
		return requests.get(f'https://www.random.org/integers/?num={number}&min=1&max={faces}&col={columns}&base=10&format=plain&rnd=new').text

	@staticmethod
	def roll_results(faces: int = 6, number: int = 1) -> str:
		"""Returns a formatted result of dice outcomes"""
		result = Random.roll(faces=int(faces), number=int(number))
		if faces == 100: # 00 - 99
			result = re.sub('100', '00', result)
			result = re.sub(r'\b(\d){1}\b', r'0\1', result) # zero pad single digit
		return f"*You rolled {number}d{faces} and got:*\n**{result}**"

	@command(
		name='roll',
		aliases=['dice']
	)
	async def roll_prefix(self, ctx: Context, query: str = '1d6'):
		"""Roll some dice (default 1d6)"""
		number, faces = query.split('d')
		if not number: # handle raw dN rolls, e.g. 'd6' or 'd20'
			number = 1
		await ctx.send(Random.roll_results(faces=int(faces), number=int(number)))
	
	@slash_command(
		name='roll',
		guild_ids=[GUILD]
	)
	async def roll_slash(self,
		ctx: discord.ApplicationContext,
		faces: Option(int, "How many faces are on each die?", min_value=1, max_value=1_000_000_000, default=6),
		number: Option(int, "How many dies should be rolled?", min_value=1, max_value=10_000, default=1)
	):
		"""Roll some dice (default 1d6)"""
		await ctx.respond(Random.roll_results(faces=faces, number=number))

# ==============================================================================

	@staticmethod
	def flip(number: int = 1) -> str:
		"""Returns a raw list of Heads or Tails outcomes"""
		result = requests.get(f'https://www.random.org/integers/?num={number}&min=1&max=2&col=1&base=10&format=plain&rnd=new').text
		result = result.replace('1', 'Heads')
		result = result.replace('2', 'Tails')
		return result
	
	@staticmethod
	def flip_results(number: int = 1) -> str:
		"""Returns a formatted result of Heads and Tails counts"""
		result = Random.flip(number)
		if len(result) == 6: # \n counts as a character and we don't strip it
			return (
				f"*You flipped {number} coins and got:*\n"
				f"**{result}**"
			)
		c = Counter(result.split('\n'))
		return (
			f"*You flipped {number} coins and got:*\n"
			f"**{c['Heads']}** Heads\n"
			f"**{c['Tails']}** Tails"
		)

	@command(
		name='flip',
		aliases=['coin']
	)
	async def flip_prefix(self, ctx: Context, number: str = 1):
		"""Flip a coin (default 1)"""
		await ctx.send(self.flip_results(number))

	@slash_command(
		name='flip',
		guild_ids=[GUILD]
		)
	async def flip_slash(self,
		ctx: discord.ApplicationContext,
		number: Option(int, "How many coins should be flipped?", min_value=1, max_value=10_000, default=1)
	):
		"""Flip a coin (default 1)"""
		await ctx.respond(self.flip_results(number))