import discord
from discord.ext.commands import Cog

def setup(bot: discord.Bot):
	bot.add_cog(Immigration(bot))

class Immigration(Cog):
	"""Logs when a Discord profile joins or leaves the guild."""

	CHANNEL = 620055960467275776

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Immigration cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(Immigration.CHANNEL)

	@Cog.listener()
	async def on_member_join(self, member: discord.Member):
		tag = member.mention
		await self.channel.send(f'{tag} has arrived! We hope you enjoy your stay.')

	@Cog.listener()
	async def on_member_remove(self, member: discord.Member):
		tag = member.mention
		await self.channel.send(f'And then, {tag} left the Discord server.')

	@Cog.listener()
	async def on_member_ban(self, guild: discord.Guild, user: discord.User):
		tag = user.mention
		await self.channel.send(f'{tag} has been exiled for their crimes against humanity!')

	@Cog.listener()
	async def on_member_unban(self, guild: discord.Guild, user: discord.User):
		tag = user.mention
		await self.channel.send(f'{tag} has been forgiven for their crimes against humanity.')