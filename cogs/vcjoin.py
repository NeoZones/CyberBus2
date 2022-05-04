import discord
from discord.ext.commands import Cog

def setup(bot: discord.Bot):
	bot.add_cog(VCJoin(bot))

class VCJoin(Cog):
	"""Log when a member joins VC, for pinging purposes"""

	CHANNEL = 620028244887994408

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		self.channel: discord.TextChannel = self.bot.get_channel(VCJoin.CHANNEL)
		print("Initialized VCJoin cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(VCJoin.CHANNEL)

	@Cog.listener()
	async def on_voice_state_update(
		self,
		member: discord.Member,
		before: discord.VoiceState,
		after: discord.VoiceState):
		"""Log when someone joins or leaves VC"""
		if before.channel == after.channel:
			return
		if not before.channel:
			embed = discord.Embed(
				description = f"**{member.display_name}** joined **{after.channel.name}**"
			)
		elif not after.channel:
			embed = discord.Embed(
				description = f"**{member.display_name}** left **{before.channel.name}**"
			)
		else:
			embed = discord.Embed(
				description = f"**{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**"
			)
		embed = embed.set_author(
				name = f"{member.display_name} ({member})",
				icon_url = member.display_avatar.url,
			)
		return await self.channel.send(embed=embed)