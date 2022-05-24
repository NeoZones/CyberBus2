import discord

""" Declare intents that the bot will use """
intents = discord.Intents.default()
intents.emojis_and_stickers = True
intents.guilds = True
intents.integrations = True
intents.message_content = True
intents.messages = True
intents.members = True
intents.presences = True
intents.reactions = True
intents.voice_states = True


""" Load the bot token """
from dotenv import load_dotenv
from os import getenv
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
GUILD = int(getenv("GUILD_ID"))

""" Initialize the bot """
from discord.ext.commands import Bot, when_mentioned_or
bot = Bot(
	command_prefix=when_mentioned_or('..', '>', '.'),
	description="A list of commands available",
	intents=intents,
	# debug_guilds=[GUILD],
	max_messages=100_000
)

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print("------")

""" Load cogs """
from os import listdir
def list_all_cogs() -> list[str]:
	return [file[:-3] for file in listdir("cogs") if file.endswith(".py")]

for cog in list_all_cogs():
	bot.load_extension(f"cogs.{cog}")

# TODO: web server for jukebox and/or soundboard?
# TODO: cog to announce when someone joins vc (maybe delete messages after some time?)
# TODO: purge messages from a user / etc? links, number, bot or human, idk
# TODO: automod? blocklist certain words or urls or whatever
# TODO: warn or kick or ban a user?
# TODO: filter the audit logs for a user? maybe?
# TODO: keep stats or levels? ehhhh

# ================================= ADMIN ======================================
from discord.commands import Option
from discord.ext.commands import Context
from discord import AutocompleteContext, ApplicationContext

async def cog_autocomplete(ctx: AutocompleteContext):
	return [cog for cog in list_all_cogs() if cog.lower().startswith( ctx.value.lower() )]

ROLE_ADMIN = 518625964763119616
ROLE_ADMIN_SFW = 727205354353721374
ME = 201046736565829632

def allowed_to_reload(ctx: Context | ApplicationContext):
	roles = [role.id for role in ctx.author.roles]
	admin = ROLE_ADMIN in roles
	sfw_admin = ROLE_ADMIN_SFW in roles
	owner = ctx.author.id == ME
	return any([admin, sfw_admin, owner])

from cogs.music import Music
def reload_music(ctx):
	music: Music = bot.get_cog("Music")
	
	q = music.q
	track = music.track
	repeat_mode = music.repeat_mode
	search_results = music.search_results
	
	bot.reload_extension(f"cogs.music")
	
	music = bot.get_cog("Music")
	
	music.q = q
	music.track = track
	music.repeat_mode = repeat_mode
	music.search_results = search_results

@bot.command(name='reload')
async def reload_prefix(ctx: Context, cog: str = None):
	"""Reload an extension (admin command)"""
	if not allowed_to_reload(ctx):
		return await ctx.send(
			"You must be an admin or bot owner to use this command"
		)
	if not cog:
		return await ctx.send("Please specify a cog to reload")
	elif cog.lower() == "music":
		reload_music(ctx)
	else:
		bot.reload_extension(f"cogs.{cog}")
	await ctx.send(f"Reloaded `{cog}` extension")

@bot.slash_command(
	name='reload',
	guild_ids=[GUILD],
)
async def reload_slash(
	ctx: ApplicationContext,
	cog: Option(str, "The cog to be reloaded", autocomplete=cog_autocomplete)
):
	"""Reload an extension (admin command)"""
	if not allowed_to_reload(ctx):
		return await ctx.respond(
			"You must be an admin or bot owner to use this command",
			ephemeral=True
		)
	if cog == "music":
		reload_music(ctx)
	else:
		bot.reload_extension(f"cogs.{cog}")
	await ctx.respond(f"Reloaded `{cog}` extension", ephemeral=True)

# ================================== END =======================================

""" Run the bot """
bot.run(TOKEN)