import discord
from discord.ext import commands

def setup(bot):
	bot.add_cog(Uwu(bot))

class Uwu(commands.Cog):
	"""uwu-ify some text"""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Uwu cog")

	@commands.command()
	async def uwu(self, ctx, *, text: str = None):
		"""uwu-ify some text

		If no text is included and the message is a reply,
		uwu-ify the replied-to message."""
		if reply := ctx.message.reference:
			text = await ctx.channel.fetch_message(reply.message_id)
			text = text.content
		if not text:
			history = await ctx.channel.history(limit=2).flatten()
			text = history[1].content
		import re, random
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
		text = re.sub('[rl]', 'w', text)
		text = re.sub('[RL]', 'W', text)
		text = re.sub('ma', 'mwa', text)
		text = re.sub('mu', 'mwu', text)
		text = re.sub('mo', 'mwo', text)
		text = re.sub('ha[sv]e?', 'haz', text)
		text = re.sub('the ', 'da ', text)
		text = re.sub('this ', 'dis ', text)
		text += random.choice(suffixes)
		await ctx.send(text)