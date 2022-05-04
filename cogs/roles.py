import discord
from discord.ext.commands import Cog
from discord.commands import slash_command, Option
from os import getenv

def setup(bot: discord.Bot):
	bot.add_cog(Roles(bot))

class Roles(Cog):
	"""Let users choose their roles"""

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Roles cog")
	
	roles = {
		'COLOR_LIGHT_RED': 608191366090063892,
		'COLOR_RED': 519029920530169857,
		'COLOR_SATAN_RED': 608084225115160616,
		'COLOR_DEEP_ORANGE': 519052968155283456,
		'COLOR_ORANGE': 519031205656788993,
		'COLOR_BROWN': 519036336351477761,
		'COLOR_PISS_YELLOW': 608084227485073418,
		'COLOR_YELLOW': 519031288422727745,
		'COLOR_LIGHT_YELLOW': 608084233327476737,
		'COLOR_LIME': 519031608997707797,
		'COLOR_MINT_GREEN': 608084229930090526,
		'COLOR_LIGHT_GREEN': 519052647278444545,
		'COLOR_GREEN': 519031954188795936,
		'COLOR_TREE_GREEN': 608084229825364014,
		'COLOR_AQUAMARINE': 519032187815985152,
		'COLOR_TEAL': 519052208080420865,
		'COLOR_CYAN': 519032473561071675,
		'COLOR_PASTEL_CYAN': 608087343030730753,
		'COLOR_LIGHT_BLUE': 519032676100079626,
		'COLOR_DISCORD_BLUE': 608087654420185104,
		'COLOR_BLUE': 519033502390550530,
		'COLOR_NAVY_BLUE': 608084227027632128,
		'COLOR_INDIGO': 519034578866929674,
		'COLOR_DEEP_PURPLE': 519053870425702430,
		'COLOR_PURPLE': 519033808180477952,
		'COLOR_MAUVE': 608084233625272332,
		'COLOR_MAGENTA': 519033938170216458,
		'COLOR_HOT_PINK': 519034420552794122,
		'COLOR_PINK': 519034029907902484,
		'COLOR_PASTEL_PINK': 608087340434325504,
		'COLOR_IVORY': 608086842428096532,
		'COLOR_WHITE': 519034129069899776,
		'COLOR_LIGHT_GRAY': 519036592254615562,
		'COLOR_BLUE_GRAY': 519055342290862080,
		'COLOR_GRAY': 519036758416031745,
		'COLOR_BLACK': 519034171058946048,
		'COLOR_INVISIBLE': 608080962043117588,
		'COLOR_H4K0R': 726069856528498738,
		'PING_ANNOUNCEMENT': 628767206989103134,
		'PING_CULT': 622168721498177587,
		'PING_VC': 765058996775550996,
		'PING_GAMING': 844985862852313131,
		'PRONOUN_HE': 692142321268949073,
		'PRONOUN_SHE': 725562073420922962,
		'PRONOUN_THEY': 692142321072078918,
	}

	@Cog.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
		guild = self.bot.get_guild(payload.guild_id)
		member = guild.get_member(payload.user_id)
		role = None
		if payload.message_id == 952489920184873030: # pronoun roles
			match payload.emoji.name:
				# 👨 = He/Him
				# 👩 = She/Her
				# 🧑 = They/Them
				case '👨':
					role = guild.get_role(self.roles['PRONOUN_HE'])
				case '👩':
					role = guild.get_role(self.roles['PRONOUN_SHE'])
				case '🧑':
					role = guild.get_role(self.roles['PRONOUN_THEY'])
		if payload.message_id == 952510538552868884: # ping roles
			match payload.emoji.name:
				# 📢 = Announcement Ping
				# 🎞️ = Cult Movie Night
				# 🎙️ = VC Ping
				# 🎮 = Gaming Ping
				case '📢':
					role = guild.get_role(self.roles['PING_ANNOUNCEMENT'])
				case '🎞️':
					role = guild.get_role(self.roles['PING_CULT'])
				case '🎙️':
					role = guild.get_role(self.roles['PING_VC'])
				case '🎮':
					role = guild.get_role(self.roles['PING_GAMING'])
		if role:
			await member.add_roles(role)

	@Cog.listener()
	async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
		guild = self.bot.get_guild(payload.guild_id)
		member = guild.get_member(payload.user_id)
		role = None
		if payload.message_id == 952489920184873030: # pronoun roles
			match payload.emoji.name:
				# 👨 = He/Him
				# 👩 = She/Her
				# 🧑 = They/Them
				case '👨':
					role = guild.get_role(self.roles['PRONOUN_HE'])
				case '👩':
					role = guild.get_role(self.roles['PRONOUN_SHE'])
				case '🧑':
					role = guild.get_role(self.roles['PRONOUN_THEY'])
				case _:
					role = None
		if payload.message_id == 952510538552868884: # ping roles
			match payload.emoji.name:
				# 📢 = Announcement Ping
				# 🎞️ = Cult Movie Night
				# 🎙️ = VC Ping
				# 🎮 = Gaming Ping
				case '📢':
					role = guild.get_role(self.roles['PING_ANNOUNCEMENT'])
				case '🎞️':
					role = guild.get_role(self.roles['PING_CULT'])
				case '🎙️':
					role = guild.get_role(self.roles['PING_VC'])
				case '🎮':
					role = guild.get_role(self.roles['PING_GAMING'])
		if role:
			await member.remove_roles(role)

	async def get_colors(self, ctx: discord.AutocompleteContext) -> list[str]:
		"""Returns a list of colors matching the partial input"""
		COLORS = [
			"Light Red",
			"Red",
			"Satan Red",
			"Deep Orange",
			"Orange",
			"Brown",
			"Piss Yellow",
			"Yellow",
			"Light Yellow",
			"Lime",
			"Mint Green",
			"Light Green",
			"Green",
			"Tree Green",
			"Aquamarine",
			"Teal",
			"Cyan",
			"Pastel Cyan",
			"Light Blue",
			"Discord Blue",
			"Blue",
			"Navy Blue",
			"Indigo",
			"Deep Purple",
			"Mauve",
			"Magenta",
			"Hot Pink",
			"Pink",
			"Pastel Pink",
			"Ivory",
			"White",
			"Light Gray",
			"Blue Gray",
			"Gray",
			"Black",
		]
		return [
			color
			for color in COLORS
			if color.lower().startswith( ctx.value.lower() )
		]

	@slash_command(
		description="Choose the color of your display name",
		guild_ids=[int(getenv("GUILD_ID"))]
	)
	async def color(
		self,
		ctx: discord.ApplicationContext,
		name: Option(str, "Color name", autocomplete=get_colors)
	):
		"""Choose the color of your display name"""
		color = "COLOR_" + name.replace(" ", "_").upper()
		if self.roles[color] == 726069856528498738:
			new_color_role = ctx.guild.get_role(self.roles[color])
			await ctx.interaction.user.add_roles(new_color_role)
			return await ctx.respond(f"You should now have the {name} role.", ephemeral=True)
		try:
			new_color_role = ctx.guild.get_role(self.roles[color])
			all_current_roles = ctx.interaction.user.roles
			old_color_roles = []
			for role in all_current_roles:
				if role.id in self.roles.values() and role.id != 726069856528498738:
					old_color_roles.append(role)
			if old_color_roles:
				await ctx.interaction.user.remove_roles(*old_color_roles)
			await ctx.interaction.user.add_roles(new_color_role)
		except KeyError:
			return await ctx.respond("Please provide a valid color name.", ephemeral=True)
		await ctx.respond(f"You should now have the {name} role.", ephemeral=True)