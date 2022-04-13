# import discord
# from discord.ext.commands import Cog

# def setup(bot):
# 	bot.add_cog(YourMom(bot))

# class YourMom(Cog):
# 	"""Old joke is old, blame pizza"""
# 	def __init__(self, bot):
# 		self.bot = bot
# 		print("Initialized YourMom cog")

# 	@Cog.listener()
# 	async def on_message(self, message):
# 		if message.author.id == self.bot.user.id:
# 			return
# 		if "doing" in message.content.lower():
# 			await message.reply("doin' your mom, doin' doin' your mom!", mention_author=False)