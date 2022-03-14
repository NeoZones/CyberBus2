import discord
from discord.ext import commands
""" Declare intents that the bot will use """
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
""" Initialize the bot """
bot = commands.Bot(
	command_prefix=commands.when_mentioned_or('..', '>', '.'),
	description="A list of commands available",
	intents=intents
)

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user} (ID: {bot.user.id})")
	print("------")

""" Load the bot token """
from dotenv import load_dotenv
load_dotenv()
import os
TOKEN = os.getenv("BOT_TOKEN")
""" Load cogs """
for file in os.listdir("cogs"):
	if not file.endswith(".py"):
		continue
	name = file[:-3]
	bot.load_extension(f"cogs.{name}")
""" Run the bot """
bot.run(TOKEN)

# TODO: web server for jukebox and/or soundboard?
# TODO: cog to announce when someone joins vc (maybe delete messages after some time?)
# TODO: purge messages from a user / etc? links, number, bot or human, idk
# TODO: automod? blocklist certain words or urls or whatever
# TODO: warn or kick or ban a user?
# TODO: filter the audit logs for a user? maybe?
# TODO: keep stats or levels? ehhhh