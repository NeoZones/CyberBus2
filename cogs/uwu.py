import discord
from discord.ext.commands import Cog, command, Context
import re, random

def setup(bot: discord.Bot):
	bot.add_cog(Uwu(bot))

class Uwu(Cog):
	"""uwu-ify some text"""
	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Uwu cog")

	@command()
	async def uwu(self, ctx: Context, *, text: str = None):
		"""uwu-ify some text

		If no text is included and the message is a reply,
		uwu-ify the replied-to message."""
		if reply := ctx.message.reference:
			message = await ctx.channel.fetch_message(reply.message_id)
			text = message.content
		if not text:
			history = await ctx.channel.history(limit=2).flatten()
			_, message = history
			text = message.content
		
		suffixes = [
			" XDDD",
			" UwU",
			"...",
			" ^_^",
			" :P",
			" :3",
			" ;)",
			" ._.",
			" xD",
			" x3",
			" ;_;",
			" (????)",
			" <3",
			" <:",
			" >w<"
		]
		text = re.sub(r'[rl]', r'w', text)
		text = re.sub(r'[RL]', r'W', text)
		text = re.sub(r'ma', r'mwa', text)
		text = re.sub(r'mu', r'mwu', text)
		text = re.sub(r'mo', r'mwo', text)
		text = re.sub(r'\bha[sv]e?\b', r'haz', text)
		text = re.sub(r'\bthe\b', r'da', text)
		text = re.sub(r'\bthis\b', r'dis', text)
		text += random.choice(suffixes)
		await ctx.send(text)