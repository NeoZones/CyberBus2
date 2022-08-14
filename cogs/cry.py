import discord
from discord.ext.commands import Cog, command, Context
import re, random
import math

LETTERS = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}
VOWELS = {'a', 'e', 'i', 'o', 'u'}
CONSONANTS = LETTERS - VOWELS
PUNCTUATION = {',', '"', ';', '.', '!', '?'}
NUMBERS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}

def chance(value: int) -> bool:
	"""Random probability check as a percentage"""
	return random.randint(0,99) < value

def transform(char: str) -> str:
	"""transform characters according to ruleset"""		
	# skip unfriendly characters
	if char not in LETTERS | NUMBERS:
		return char

	# apostrophe to semicolons
	if char == "'" and chance(40):
		return ';' * random.randint(1,3)

	# add 3 random punctuations
	if chance(5):
		return char + random.choice(tuple(PUNCTUATION)) * random.randint(1,3)

	# add a second vowel
	if char in VOWELS and chance(5):
		return char * 2

	# multiply some consonants
	if char in CONSONANTS and chance(10):
		return char * random.randint(1,4)

	# doubles a character
	if chance(10):
		return char * 2

	# deletes a character
	if chance(1):
		return ''

	# add a random character
	if chance(1):
		return random.choice(tuple(LETTERS | PUNCTUATION))

	# add random spacing
	if chance(5):
		return char + ' '

	# if all random checks fail then mostly return unchanged
	return char

def cryify(text: str) -> str:
	"""Convert input into crytype. based on dead-bird/apcry with mods"""
	# preliminary substitutions
	text = text.lower()
	text = re.sub(r'(\w+)(ing)', r'\1in', text) # (word)ing -> (word)in
	# text = re.sub(r'\bplease\b', r'pls', text) # please -> pls
	# text = re.sub(r'\byou\b', r'u', text) # you -> u
	# text = re.sub(r'\bto be honest\b', r'tbh', text) # to be honest -> tbh
	# text = re.sub(r'\bi don\'t know\b', r'idk', text) # i don't know -> idk
	# text = re.sub(r"'", r';', text) # apostrophe to semicolon
	# text = re.sub(r'.', r'...', text) # triple any periods
	# text = re.sub(r';', r';;;', text) # triple semicolons
	# text = re.sub(r',', r',,,', text) # triple commas

	# transform text into output
	output = ''
	for index, char in enumerate(text):
		if chance(5):
			try: 
				output = output + text[index+1] + char
				continue
			except:
				pass
		output += transform(char)
	return output

def setup(bot: discord.Bot):
	bot.add_cog(Cry(bot))

class Cry(Cog):
	"""crytype-ify some text"""
	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		print("Initialized Cry cog")

	@command()
	async def cry(self, ctx: Context, *, text: str = None):
		"""crytype-ify some text

		If no text is included and the message is a reply,
		uses the replied-to message."""
		if reply := ctx.message.reference:
			message = await ctx.channel.fetch_message(reply.message_id)
			text = message.content
		if not text:
			history = await ctx.channel.history(limit=2).flatten()
			_, message = history
			text = message.content

		await ctx.send(cryify(text))