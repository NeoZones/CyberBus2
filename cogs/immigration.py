import discord
from discord.ext import commands

def setup(bot):
	bot.add_cog(Immigration(bot))

class Immigration(commands.Cog):
	"""Logs when a Discord profile joins or leaves the guild."""
	def __init__(self, bot):
		self.bot = bot
		print("Initialized Immigration cog")

	@commands.Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(620055960467275776)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		tag = member.mention
		await self.channel.send(f'{tag} has arrived! We hope you enjoy your stay.')

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		tag = member.mention
		await self.channel.send(f'And then, {tag} left the Discord server.')

	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		tag = user.mention
		await self.channel.send(f'{tag} has been exiled for their crimes against humanity!')

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		tag = user.mention
		await self.channel.send(f'{tag} has been forgiven for their crimes against humanity.')