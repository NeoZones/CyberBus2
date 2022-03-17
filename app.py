import discord
from discord.ext.commands import Bot, when_mentioned_or

""" Declare intents that the bot will use """
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

""" Load the bot token """
from dotenv import load_dotenv
load_dotenv()
from os import getenv
TOKEN = getenv("BOT_TOKEN")
GUILD = getenv("GUILD_ID")

""" Initialize the bot """
bot = Bot(
	command_prefix=when_mentioned_or('..', '>', '.'),
	description="A list of commands available",
	intents=intents,
	debug_guilds=[GUILD]
)

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print("------")

""" Load cogs """
from os import listdir
def list_cogs():
	cog_list = []
	for file in listdir("cogs"):
		if not file.endswith(".py"):
			continue
		cog_list.append(file[:-3])
	return cog_list

cogs = list_cogs()
for cog in cogs:
	bot.load_extension(f"cogs.{cog}")

# TODO: web server for jukebox and/or soundboard?
# TODO: cog to announce when someone joins vc (maybe delete messages after some time?)
# TODO: purge messages from a user / etc? links, number, bot or human, idk
# TODO: automod? blocklist certain words or urls or whatever
# TODO: warn or kick or ban a user?
# TODO: filter the audit logs for a user? maybe?
# TODO: keep stats or levels? ehhhh

# ================================= ADMIN ======================================
from discord.commands import Option, permissions

ROLE_ADMIN = 518625964763119616
ROLE_ADMIN_SFW = 727205354353721374
ME = 201046736565829632

async def cog_autocomplete(ctx: discord.AutocompleteContext):
	return list_cogs()

# @bot.command(name='reload')
# @permissions.permission(role_id=ROLE_ADMIN, permission=True)
# @permissions.permission(role_id=ROLE_ADMIN_SFW, permission=True)
# @permissions.permission(user_id=ME, permission=True)
# async def reload_prefix(ctx, cog: str = None):
# 	"""Reload an extension (admin command)"""
# 	if not cog:
# 		return await ctx.send("Please specify a cog to reload")
# 	bot.reload_extension(f"cogs.{cog}")
# 	await ctx.send(f"Reloaded `{cog}` extension")

@bot.slash_command(
	name='reload',
	guild_ids=[GUILD],
	permissions=[
		permissions.CommandPermission(id=ME, type=2, permission=True),
		permissions.CommandPermission(id=ROLE_ADMIN, type=1, permission=True),
		permissions.CommandPermission(id=ROLE_ADMIN_SFW, type=1, permission=True),
	]
)
async def reload_slash(
	ctx: discord.ApplicationContext,
	cog: Option(str, "The cog to be reloaded", autocomplete=cog_autocomplete)
):
	"""Reload an extension (admin command)"""
	bot.reload_extension(f"cogs.{cog}")
	await ctx.respond(f"Reloaded `{cog}` extension", ephemeral=True)

# ================================== END =======================================

""" Run the bot """
bot.run(TOKEN)