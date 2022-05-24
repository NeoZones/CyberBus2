import discord
from discord.ext.commands import Cog
from datetime import timedelta
from os import getenv, path, makedirs
import logging

if not path.exists('.logs'):
		makedirs('.logs')
		
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
fh = logging.FileHandler('.logs/audit.log')
formatter = logging.Formatter('%(asctime)s | %(name)s | [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
if not len(logger.handlers):
	logger.addHandler(fh)

def setup(bot: discord.Bot):
	bot.add_cog(Audit(bot))

class Audit(Cog):
	"""Posts events from the audit log to a specified channel."""

	CHANNEL = 519071523714367489 # server-log channel
	#CHANNEL = 951378341162807387 # bot-test channel

	def __init__(self, bot: discord.Bot):
		self.bot: discord.Bot = bot
		self.channel: discord.TextChannel = self.bot.get_channel(Audit.CHANNEL)
		print("Initialized Audit cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(Audit.CHANNEL)

	# MESSAGES ==================================================================

	@Cog.listener()
	async def on_message_delete(
		self,
		message: discord.Message):
		"""Log deleted messages (if in cache)"""
		logger.info("on_message_delete received")
		logger.debug(f"{message=}")
		if message.author.id in set(
			[
				647368715742216193, # SaucyBot
	 			self.bot.user.id,
			]
		):
			logger.info("on_message_delete ignored\n")
			return # ignore deleted messages from the above members

		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Message deleted",
				colour = 0xff0000,
			).add_field(
				name = "Channel",
				value = message.channel.mention,
				inline = False,
			).add_field(
				name = "Content",
				value = message.content if message.content else "[No content]",
				inline = False,
			).set_author(
				name = f"{message.author.display_name} ({message.author})",
				icon_url = message.author.display_avatar.url
			).set_footer(
				text = f"Message {message.id} in channel {message.channel.id} was deleted",
			)
		)
		if msg:
			logger.info("on_message_delete sent to channel\n")

	# @Cog.listener()
	# async def on_raw_message_delete(self, payload):
	# 	"""Log deleted messages"""

	# 	guild_id = payload.guild_id
	# 	channel_id = payload.channel_id
	# 	message_id = payload.message_id

	# 	author = None
	# 	content = None
	# 	if payload.cached_message:
	# 		author = payload.cached_message.author
	# 		content = payload.cached_message.content
	# 		if author.id in set(
	# 			[
	# 			647368715742216193, # SaucyBot
	# 			self.bot.user.id,
	# 			]
	# 		):
	# 			return # ignore deleted messages from the above members

	# 	await self.channel.send(
	# 		embed = discord.Embed(
	# 			title = "Message deleted",
	# 			colour = 0xff0000,
	# 		).add_field(
	# 			name = "Channel",
	# 			value = f"<#{channel_id}>",
	# 			inline = False,
	# 		).add_field(
	# 			name = "Content",
	# 			value = content if content else "[No content found in cache]",
	# 			inline = False,
	# 		).set_author(
	# 			name = f"{author.display_name} ({author})" if author else f"[Message too old]",
	# 			icon_url = author.display_avatar.url if author else self.bot.user.default_avatar,
	# 		).set_footer(
	# 			text = f"Message {message_id} in channel {channel_id} was deleted",
	# 		)
	# 	)

	@Cog.listener()
	async def on_message_edit(
		self,
		before: discord.Message,
		after: discord.Message):
		"""Log edited and updated messages (if in cache)"""
		logger.info("on_message_edit received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		if after.author.id in [
			823849032908668998, # SocialFeeds#0000
			647368715742216193, # SaucyBot
		]:
			logger.info("on_message_edit ignored: socialfeeds or saucybot\n")
			return

		embed = discord.Embed(
			title = "Message updated",
			url = after.jump_url,
			colour = 0xffff00,
		).set_author(
			name = f"{after.author.display_name} ({after.author})",
			icon_url = after.author.display_avatar.url,
		).set_footer(
			text = f"Message ID: {after.id} | Channel ID: {after.channel.id}",
		)

		if before.embeds != after.embeds and after.embeds and not before.embeds: # embeds added
			logger.info("on_message_edit ignored: embeds were added\n")
			return # we don't care

		if before.content != after.content: # content changed
			logger.info("content was changed")
			embed.description = "Content was changed"
			embed = embed.add_field(
				name = "Before",
				value = before.content if before.content else "[No content]",
				inline = False,
			).add_field(
				name = "After",
				value = after.content if after.content else "[No content]",
				inline = False,
			)
			msg = await self.channel.send(embed=embed)
			if msg:
				logger.info("on_message_edit sent to channel\n")
			return

		if before.embeds != after.embeds and before.embeds and not after.embeds: # embeds removed
			logger.info("embed was changed")
			logger.debug(f"{before.embeds=}")
			logger.debug(f"{after.embeds=}")
			embed.description = "Embed was removed"
			embed = embed.add_field(
				name = "Content",
				value = after.content if after.content else "[No content]",
			)
			msg = await self.channel.send(embed=embed)
			if msg:
				logger.info("on_message_edit sent to channel\n")
			return
			
		logger.debug(f"{hash(before)=}")
		logger.debug(f"{hash(after)=}")
		attrs = [f for f in dir(after) if not f.startswith('_') and not callable(getattr(after,f))]
		for attr in attrs:
			logger.debug(f"Comparing {attr} in before/after")
			value_before = getattr(before, attr)
			value_after = getattr(after, attr)
			logger.debug(f"{value_before=}")
			logger.debug(f"{value_after=}")
			if value_before != value_after:
				logger.warning(f"{attr} not equal")
			subattrs = [f for f in dir(getattr(before, attr)) if not f.startswith('_') and not callable(getattr(getattr(before, attr),f))]
			for subattr in subattrs:
				logger.debug(f"Comparing {attr}.{subattr} in before/after")
				value_before = getattr(before, attr)
				if value_before:
					value_before = getattr(value_before, subattr)
				value_after = getattr(after, attr)
				if value_after:
					value_after = getattr(value_after, subattr)
				logger.debug(f"{value_before=}")
				logger.debug(f"{value_after=}")
				if value_before != value_after:
					logger.warning(f"{attr}.{subattr} not equal")
		logger.warning("on_message_edit not handled\n")

	# @Cog.listener()
	# async def on_raw_message_edit(self, payload):
	# 	"""Log edited and updated messages"""

	# 	guild_id = payload.guild_id
	# 	channel_id = payload.channel_id
	# 	message_id = payload.message_id

	# 	url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

	# 	embed = discord.Embed(
	# 		title = "Message updated",
	# 		url = url,
	# 		colour = 0xffff00,
	# 	)

	# 	if not payload.cached_message:
	# 		embed.description = "[Message not in cache, so no details could be loaded]"
	# 		return await self.channel.send(embed = embed)

	# 	if "pinned" in payload.data:
	# 		if not payload.cached_message.pinned and payload.data['pinned']:
	# 			return

	# 	"""Add author"""
	# 	author = payload.cached_message.author
	# 	if author.id == 823849032908668998: # SocialFeeds#0000
	# 		return
	# 	embed = embed.set_author(
	# 		name = f"{author.display_name} ({author})",
	# 		icon_url = author.display_avatar.url,
	# 	)

	# 	"""Check for content changes"""
	# 	if "content" in payload.data:
	# 		content_before = payload.cached_message.content
	# 		content_after = payload.data['content']
	# 		if content_before and content_after and content_before != content_after:
	# 			embed.description = "Content changed"
	# 			embed = embed.add_field(
	# 				name = "Before",
	# 				value = content_before,
	# 				inline = False,
	# 			).add_field(
	# 				name = "After",
	# 				value = content_after,
	# 				inline = False,
	# 			).set_footer(
	# 				text = f"Message {message_id} in channel {channel_id} was edited",
	# 			).add_field(
	# 				name = "Original channel",
	# 				value = f"<#{channel_id}>",
	# 			)
	# 			return await self.channel.send(embed = embed)

	# 	"""Check for embeds"""
	# 	if "embeds" in payload.data:
	# 		embeds_before = payload.cached_message.embeds
	# 		embeds_after = payload.data['embeds']
	# 		if embeds_after and not embeds_before:
	# 			return
	# 		if embeds_before and not embeds_after:
	# 			embed = embed.set_footer(
	# 				text = f"Message {message_id} in channel {channel_id} had an embed removed"
	# 			).add_field(
	# 				name = "Original channel",
	# 				value = f"<#{channel_id}>",
	# 			)
	# 			return await self.channel.send(embed = embed)

	# 	print("=== Message updated, but how? ===")
	# 	print(len(f"{payload.data=}"))
	# 	print(f"{payload.data=}")
	# 	print("")
	# 	print(len(f"{payload.cached_message=}"))
	# 	print(f"{payload.cached_message=}")

	# CHANNELS ==================================================================

	@Cog.listener()
	async def on_guild_channel_create(
		self,
		channel: discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel):
		"""Log created channels"""
		logger.info("on_guild_channel_create received")
		logger.debug(f"{channel=}")
		url = f"https://discord.com/channels/{channel.guild.id}/{channel.id}"
		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Channel created",
				url = url,
				colour = 0x00ff00,
			).set_author(
				name = f"#{channel.name}",
				url = url,
			).set_footer(
				text = f"The channel {channel.id} was created",
			)
		)
		if msg:
			logger.info("on_guild_channel_create sent to channel\n")

	@Cog.listener()
	async def on_guild_channel_delete(
		self,
		channel: discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel):
		"""Log deleted channels"""
		logger.info("on_guild_channel_delete received")
		logger.debug(f"{channel=}")
		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Channel deleted",
				colour = 0xff0000,
			).set_author(
				name = f"#{channel.name}",
			).set_footer(
				text = f"The channel {channel.id} was deleted",
			)
		)
		if msg:
			logger.info("on_guild_channel_delete sent to channel\n")

	@Cog.listener()
	async def on_guild_channel_update(
		self,
		before: discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel,
		after: discord.abc.GuildChannel | discord.TextChannel | discord.VoiceChannel):
		"""Log updated channels"""
		logger.info("on_guild_channel_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		if after.id == 857144133742493736: # minecraft channel
			logger.info("on_guild_channel_update ignored\n")
			return

		url = f"https://discord.com/channels/{after.guild.id}/{after.id}"
		embed = discord.Embed(
				title = "Channel updated",
				description = "The following changes were made:\n",
				url = url,
				colour = 0xffff00,
			).set_author(
				name = f"#{before.name}",
			).set_footer(
				text = f"Channel ID: {after.id}"
			)

		if before.name != after.name:
			logger.info("name not equal")
			embed.description += f"- Channel name changed from `{before.name}` to `{after.name}`\n"
			embed.set_author(
				name = f"#{before.name} -> {after.name}"
			)

		if before.category_id != after.category_id:
			logger.info("category_id not equal")
			logger.debug(f"{before.category_id=}")
			logger.debug(f"{after.category_id=}")
			embed.description += f"- {after.mention} changed category from {before.category} to {after.category}\n"
		
		if before.changed_roles != after.changed_roles:
			logger.info("changed_roles not equal")
			logger.debug(f"{before.changed_roles=}")
			logger.debug(f"{after.changed_roles=}")
			roles_before = set(before.changed_roles)
			roles_after = set(after.changed_roles)
			roles_added = roles_after - roles_before
			roles_removed = roles_before - roles_after
			if roles_added or roles_removed:
				logger.debug(f"{roles_added=}")
				logger.debug(f"{roles_removed=}")
				embed.description += f"- {after.mention} changed roles\n"
				for role in roles_added:
					embed.description += f"  + {role}\n"
				for role in roles_removed:
					embed.description += f"  - {role}\n"

		if before.members != after.members:
			logger.info("members not equal")
			logger.debug(f"{before.members=}")
			logger.debug(f"{after.members=}")
			embed.description += f"- {after.mention} changed members from {before.members} to {after.members}\n"

		if after.nsfw and not before.nsfw:
			logger.info("nsfw: false -> true")
			embed.description += f"- {after.mention} was marked as NSFW\n"
		if before.nsfw and not after.nsfw:
			logger.info("nsfw: true -> false")
			embed.description += f"- {after.mention} was unmarked as NSFW\n"

		if before.overwrites != after.overwrites:
			logger.info("overwrites not equal")
			logger.debug(f"{before.overwrites=}")
			logger.debug(f"{after.overwrites=}")
			embed.description += f"- {after.mention} changed overwrites\n"
			# figure out which roles or members changed
			changed_rm = set()
			removed_rm = set()
			added_rm = set()
			for role_or_member in before.overwrites: # dict[rm] = po
				if role_or_member in after.overwrites: # dict[rm] = po
					changed_rm.add(role_or_member)
				else:
					removed_rm.add(role_or_member)
			for role_or_member in after.overwrites:
				if role_or_member not in before.overwrites:
					added_rm.add(role_or_member)
			# compare changed perms
			logger.debug(f"{added_rm=}")
			for rm in added_rm:
				overwrites_added = after.overwrites[rm]
				logger.debug(f"{overwrites_added=}")
				for overwrite in overwrites_added:
					logger.debug(f"{overwrite=}")
					for perm, value in overwrite:
						embed.description += f"+ {perm}: {value}\n"
			logger.debug(f"{changed_rm=}")
			for rm in changed_rm:
				pb = set(before.overwrites[rm]) # PermissionOverwrite set
				pa = set(after.overwrites[rm]) # aka {(perm, value),(...)}
				overwrites_added = pa - pb 
				overwrites_removed = pb - pa
				logger.debug(f"{overwrites_added=}")
				for overwrite in overwrites_added:
					logger.debug(f"{overwrite=}")
					for perm, value in overwrite:
						embed.description += f"+ {perm}: {value}\n"
				logger.debug(f"{overwrites_removed=}")
				for overwrite in overwrites_removed:
					logger.debug(f"{overwrite=}")
					for perm, value in overwrite:
						embed.description += f"- {perm}: {value}\n"
			logger.debug(f"{removed_rm=}")
			for rm in removed_rm:
				overwrites_removed = before.overwrites[rm]
				logger.debug(f"{overwrites_removed=}")
				for overwrite in overwrites_removed:
					logger.debug(f"{overwrite=}")
					for perm, value in overwrite:
						embed.description += f"- {perm}: {value}\n"				

		if after.permissions_synced and not before.permissions_synced:
			logger.info("permissions_synced: false -> true")
			embed.description += f"- Permissions for {after.mention} were synced with {after.category}\n"
		if before.permissions_synced and not after.permissions_synced:
			logger.info("permissions_synced: true -> false")
			embed.description += f"- Permissions for {after.mention} were unsynced with {after.category}\n"

		if before.type != after.type:
			logger.info("type not equal")
			logger.debug(f"{before.type=}")
			logger.debug(f"{after.type=}")
			embed.description = f"- The channel type of {after.mention} was changed from {before.type} to {after.type}\n"

		if before.type != discord.ChannelType.voice:

			if before.default_auto_archive_duration != after.default_auto_archive_duration:
				logger.info("default_auto_archive_duration not equal")
				logger.debug(f"{before.default_auto_archive_duration=}")
				logger.debug(f"{after.default_auto_archive_duration=}")
				embed.description += f"- {after.mention} changed auto-archive duration from {before.default_auto_archive_duration} minutes to {after.default_auto_archive_duration} minutes\n"

			if before.slowmode_delay != after.slowmode_delay:
				logger.info("slowmode_delay not equal")
				logger.debug(f"{before.slowmode_delay=}")
				logger.debug(f"{after.slowmode_delay=}")
				embed.description += f"- Slowmode delay for {after.mention} was changed from {before.slowmode_delay} seconds to {after.slowmode_delay} seconds\n"

			if before.topic != after.topic:
				logger.info("topic not equal")
				logger.debug(f"{before.topic=}")
				logger.debug(f"{after.topic=}")
				embed.description += f"- Topic changed for {after.mention}\n"
				embed = embed.add_field(
					name = "Before",
					value = before.topic,
					inline = False,
				).add_field(
					name = "After",
					value = after.topic,
					inline = False
				)

		# if after.type == discord.ChannelType.voice:
		# 	pass
		# 	if before.bitrate != after.bitrate:
		# 		pass
		# 	if before.rtc_region != after.rtc_region:
		# 		pass
		# 	if before.user_limit != after.user_limit:
		# 		pass
		# 	if before.video_quality_mode != after.video_quality_mode:
		# 		pass

		if embed.description == "The following changes were made:\n":
			logger.warning("on_guild_channel_update had no changes detected\n")
			logger.debug(f"{hash(before)=}")
			logger.debug(f"{hash(after)=}")
			attrs = [f for f in dir(after) if not f.startswith('_') and not callable(getattr(after,f))]
			for attr in attrs:
				logger.debug(f"Comparing {attr} in before/after")
				value_before = getattr(before, attr)
				value_after = getattr(after, attr)
				if value_before != value_after:
					logger.warning(f"{attr} not equal")
					logger.debug(f"{value_before=}")
					logger.debug(f"{value_after=}")
			return # the change made is one we don't care about or haven't handled

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_guild_channel_update sent to channel\n")

	# @Cog.listener()
	# async def on_guild_channel_pins_update(self, channel, last_pin):
	# 	"""Log pinning and unpinning messages"""
	# 	pass
	# ^^^ this is handled by the Unpin extension now

	# THREADS ===================================================================

	# Skip for now...
	# on_thread_join(self, thread)
	# on_thread_remove(self, thread)
	
	# @Cog.listener()
	# async def on_raw_thread_delete(self, payload):
	#	pass
	
	# on_thread_member_join(self, member)
	# on_thread_member_remove(self, member)
	# on_thread_update(self, before, after)

	# INTEGRATIONS ==============================================================

	@Cog.listener()
	async def on_integration_create(
		self,
		integration: discord.Integration | discord.BotIntegration):
		"""Log created integrations"""
		logger.info("on_integration_create received")
		logger.debug(f"{integration=}")
		embed = discord.Embed(
			title = "Integration created",
			description = f"{integration.user} added an integration for {integration.name}",
			colour = 0x00ff00,
		).set_author(
			name = integration.name,
		).add_field(
			name = "Integration type",
			value = integration.type,
		).add_field(
			name = "Enabled",
			value = integration.enabled,
		).add_field(
			name = "Integration account",
			value = f"<@{integration.account.id}>"
		).set_footer(
			text = f"{integration.user.display_name} ({integration.user}) added an integration for {integration.name}",
			icon_url = integration.user.display_avatar.url,
		)

		if integration.type == "discord":
			embed = embed.set_author(
				name = f"{integration.application.user.display_name} ({integration.application.user})",
				icon_url = integration.application.user.display_avatar.url,
			)

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_integration_create sent to channel\n")

	@Cog.listener()
	async def on_integration_update(
		self,
		integration: discord.Integration | discord.BotIntegration):
		"""Log updated integrations""" # when is this actually called???
		logger.info("on_integration_update received")
		logger.debug(f"{integration=}")
		embed = discord.Embed(
			title = "Integration updated",
			colour = 0x00ff00,
		).set_author(
			name = integration.name,
		).add_field(
			name = "Integration account",
			value = f"<@{integration.account.id}>"
		).add_field(
			name = "Integration type",
			value = integration.type,
		).add_field(
			name = "Enabled",
			value = integration.enabled,
		).set_footer(
			text = f"{integration.user.display_name} ({integration.user}) updated an integration for {integration.name}",
			icon_url = integration.user.display_avatar.url,
		)

		if integration.type == "discord":
			embed = embed.set_author(
				name = f"{integration.application.user.display_name} ({integration.application.user})",
				icon_url = integration.application.user.display_avatar.url,
			)

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_integration_update sent to channel\n")

	@Cog.listener()
	async def on_raw_integration_delete(self, payload: discord.RawIntegrationDeleteEvent):
		"""Log deleted integrations"""
		logger.info("on_raw_integration_delete received")
		logger.debug(f"{payload=}")
		user = await self.bot.fetch_user(payload.application_id)
		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Integration deleted",
				colour = 0xff0000,
			).set_footer(
				text = f"Integration {payload.integration_id} for application {payload.application_id} was deleted",
			).set_author(
				name = f"{user.display_name} ({user})",
				icon_url = user.display_avatar.url,
			).add_field(
				name = "Integration account",
				value = f"{user.mention}",
			)
		)
		if msg:
			logger.info("on_raw_integration_delete sent to channel\n")

	# MEMBERS ===================================================================

	# @Cog.listener()
	# async def on_member_join(self, member):
	# 	"""Log joining members"""
	# 	# we use the Immigration extension for this

	# @Cog.listener()
	# async def on_member_remove(self, member):
	# 	"""Log leaving members"""
	# 	# we use the Immigration extension for this

	@Cog.listener()
	async def on_member_update(
		self,
		before: discord.Member,
		after: discord.Member):
		"""Log updated members (nicknames, roles, timeouts, permissions)"""
		logger.info("on_member_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		embed = discord.Embed(
			title = "Member updated",
			colour = after.colour.value,
		).set_author(
			name = f"{after.display_name} ({after})",
			icon_url = after.display_avatar.url,
		).set_footer(
			text = f"Member ID: {after.id}",
		)

		if before.nick != after.nick: # tested working
			logger.info("nick not equal")
			logger.debug(f"{before.nick=}")
			logger.debug(f"{after.nick=}")
			embed.description = f"{after.mention} had their nickname changed"
			embed = embed.add_field(
				name = "Before",
				value = before.nick,
			).add_field(
				name = "After",
				value = after.nick,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return
		
		if before.roles != after.roles: # tested working
			logger.info("roles not equal")
			logger.debug(f"{before.roles=}")
			logger.debug(f"{after.roles=}")
			before_roles = set(before.roles)
			after_roles = set(after.roles)
			added_roles = list(after_roles - before_roles)
			removed_roles = list(before_roles - after_roles)
			logger.debug(f"{added_roles=}")
			logger.debug(f"{removed_roles=}")
			added = "\n".join([role.mention for role in added_roles])
			removed = "\n".join([role.mention for role in removed_roles])
			embed.description = f"{after.mention} had their roles updated"
			if added_roles:
				embed = embed.add_field(
					name = "Added roles",
					value = added,
				)
			if removed_roles:
				embed = embed.add_field(
				name = "Removed roles",
				value = removed,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return

		if before.name != after.name or before.discriminator != after.discriminator:
			logger.info("name or discriminator not equal")
			logger.debug(f"{before.name=}")
			logger.debug(f"{after.name=}")
			logger.debug(f"{before.discriminator=}")
			logger.debug(f"{after.discriminator=}")
			embed.description = f"{after.mention} changed their handle"
			embed = embed.add_field(
				name = "Before",
				value = before,
			).add_field(
				name = "After",
				value = after,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return

		# haven't gotten this to work... before == after for some reason,
		# even after updating my avatar multiple times.
		# maybe on_user_update?
		# if before.display_avatar.url != after.display_avatar.url:
		# 	logger.info("display_avatar.url not equal")
		# 	embed.description = f"{after.mention} changed their avatar"
		# 	embed = embed.add_field(
		# 		name = "New avatar URL",
		# 		value = after.display_avatar.url,
		# 	)
		# 	msg =  await self.channel.send(embed = embed)
		# 	if msg:
		# 		logger.info("on_member_update sent to channel\n")
		# 	return

		if after.timed_out and not before.timed_out: # idk how to time out people
			logger.info("timed_out: false -> true")
			embed.description = f"{after.mention} is now timed out"
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return
			
		elif before.timed_out and not after.timed_out:
			logger.info("timed_out: true -> false")
			embed.description = f"{after.mention} is no longer timed out"
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return

		elif before.communication_disabled_until != after.communication_disabled_until:
			logger.info("communication_disabled_until not equal")
			logger.debug(f"{before.communication_disabled_until=}")
			logger.debug(f"{after.communication_disabled_until=}")
			embed.description = f"{after.mention} had their timeout duration changed"
			embed = embed.add_field(
				name = "Before",
				value = before.communication_disabled_until,
			).add_field(
				name = "After",
				value = after.communication_disabled_until,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return

		if before.guild_permissions != after.guild_permissions: # when?
			logger.info("guild_permissions not equal")
			logger.debug(f"{before.guild_permissions=}")
			logger.debug(f"{after.guild_permissions=}")
			changed_permissions = []
			for b, a in zip(before.guild_permissions, after.guild_permissions):
				if b != a:
					changed_permissions.append((b[0], b[1], a[1]))
			logger.debug(f"{changed_permissions=}")
			added_permissions = []
			removed_permissions = []
			for p in changed_permissions:
				perm, value_before, value_after = p
				if value_after and not value_before:
					added_permissions.append(perm)
				elif value_before and not value_after:
					removed_permissions.append(perm)
			if added_permissions or removed_permissions:
				logger.debug(f"{added_permissions=}")
				logger.debug(f"{removed_permissions=}")
				embed.description = f"{after.mention} had their permissions changed"
			if added_permissions:
				embed = embed.add_field(
					name = "Permissions added",
					value = "\n".join(added_permissions)
				)
			if removed_permissions:
				embed = embed.add_field(
					name = "Permissions removed",
					value = "\n".join(removed_permissions)
				)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_member_update sent to channel\n")
			return

		# logger.debug(f"{hash(before)=}")
		# logger.debug(f"{hash(after)=}")
		# attrs = [f for f in dir(after) if not f.startswith('_') and not callable(getattr(after,f))]
		# for attr in attrs:
		# 	logger.debug(f"Comparing {attr} in before/after")
		# 	value_before = getattr(before, attr)
		# 	value_after = getattr(after, attr)
		# 	logger.debug(f"{value_before=}")
		# 	logger.debug(f"{value_after=}")
		# 	if value_before != value_after:
		# 		logger.warning(f"{attr} not equal")
		# 	subattrs = [f for f in dir(getattr(before, attr)) if not f.startswith('_') and not callable(getattr(getattr(before, attr),f))]
		# 	for subattr in subattrs:
		# 		logger.debug(f"Comparing {attr}.{subattr} in before/after")
		# 		value_before = getattr(before, attr)
		# 		if value_before:
		# 			value_before = getattr(value_before, subattr)
		# 		value_after = getattr(after, attr)
		# 		if value_after:
		# 			value_after = getattr(value_after, subattr)
		# 		logger.debug(f"{value_before=}")
		# 		logger.debug(f"{value_after=}")
		# 		if value_before != value_after:
		# 			logger.warning(f"{attr}.{subattr} not equal")
		logger.warning("on_member_update not handled\n")

	@Cog.listener()
	async def on_user_update(
		self,
		before: discord.User,
		after: discord.User):
		"""Log updated users (username, avatar, discriminator)"""

		logger.info("on_user_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		embed = discord.Embed(
			title = "User updated",
			colour = after.colour.value,
		).set_author(
			name = f"{after.display_name} ({after})",
			icon_url = after.display_avatar.url,
		).set_footer(
			text = f"User ID: {after.id}",
		)

		if before.display_avatar.url != after.display_avatar.url:
			logger.info("display_avatar.url not equal")
			embed.description = f"{after.mention} changed their avatar"
			embed = embed.add_field(
				name = "New avatar URL",
				value = after.display_avatar.url,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_user_update sent to channel\n")
			return

		if before.name != after.name or before.discriminator != after.discriminator:
			logger.info("name or discriminator not equal")
			logger.debug(f"{before.name=}")
			logger.debug(f"{after.name=}")
			logger.debug(f"{before.discriminator=}")
			logger.debug(f"{after.discriminator=}")
			embed.description = f"{after.mention} changed their handle"
			embed = embed.add_field(
				name = "Before",
				value = before,
			).add_field(
				name = "After",
				value = after,
			)
			msg =  await self.channel.send(embed = embed)
			if msg:
				logger.info("on_user_update sent to channel\n")
			return

	# ROLES =====================================================================

	@Cog.listener()
	async def on_guild_role_create(
		self,
		role: discord.Role):
		"""Log created roles"""
		logger.info("on_guild_role_create received")
		logger.debug(f"{role=}")
		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Role created",
				colour = role.colour if role.colour else 0x00ff00,
			).set_author(
				name = role.name,
				icon_url = role.icon if role.icon else self.bot.user.default_avatar,
			).set_footer(
				text = f"Role ID: {role.id}",
			).add_field(
				name = "Role link",
				value = role.mention,
			)
		)
		if msg:
			logger.info("on_guild_role_create sent to channel\n")

	@Cog.listener()
	async def on_guild_role_delete(
		self,
		role: discord.Role):
		"""Log deleted roles"""
		logger.info("on_guild_role_delete received")
		logger.debug(f"{role=}")
		msg = await self.channel.send(
			embed = discord.Embed(
				title = "Role deleted",
				colour = role.colour if role.colour else 0x00ff00,
			).set_author(
				name = role.name,
				icon_url = role.icon if role.icon else self.bot.user.default_avatar,
			).set_footer(
				text = f"Role ID: {role.id}",
			).add_field(
				name = "Role originally created at",
				value = role.created_at,
			)
		)
		if msg:
			logger.info("on_guild_role_delete sent to channel\n")

	@Cog.listener()
	async def on_guild_role_update(
		self,
		before: discord.Role,
		after: discord.Role):
		"""Log updated roles"""
		logger.info("on_guild_role_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		embed = discord.Embed(
			title = "Role updated",
			description = "The following changes were made:\n",
			colour = after.colour if after.colour else 0xffff00,
		).set_author(
			name = after.name,
			icon_url = after.icon if after.icon else self.bot.user.default_avatar,
		).set_footer(
			text = f"Role ID: {after.id}",
		)

		if before.name != after.name:
			logger.info("name not equal")
			logger.debug(f"{before.name=}")
			logger.debug(f"{after.name=}")
			embed.description = f"- {after.mention} was renamed"
			embed = embed.add_field(
				name = "Before",
				value = before.name,
			).add_field(
				name = "After",
				value = after.name,
			)

		if before.colour != after.colour:
			logger.info("colour not equal")
			logger.debug(f"{before.colour=}")
			logger.debug(f"{after.colour=}")
			embed.description = f"- {after.mention} had its colour changed from {before.colour} to {after.colour}\n"

		if after.hoist and not before.hoist:
			logger.info("hoist: false -> true")
			embed.description = f"- {after.mention} was hoisted; it will now show above online users\n"
		elif before.hoist and not after.hoist:
			logger.info("hoist: true -> false")
			embed.description = f"- {after.mention} was unhoisted; it will no longer show above online users\n"

		if before.permissions != after.permissions: # when an integration is updated, e.g.
			logger.info("permissions not equal")
			logger.debug(f"{before.permissions=}")
			logger.debug(f"{after.permissions=}")
			changed_permissions = []
			for b, a in zip(before.permissions, after.permissions):
				if b != a:
					changed_permissions.append((b[0], b[1], a[1]))
			logger.debug(f"{changed_permissions=}")
			added_permissions = []
			removed_permissions = []
			for p in changed_permissions:
				perm, value_before, value_after = p
				if value_after and not value_before:
					added_permissions.append(perm)
				elif value_before and not value_after:
					removed_permissions.append(perm)
			if added_permissions or removed_permissions:
				embed.description = f"{after.mention} had its permissions changed"
			if added_permissions:
				logger.debug(f"{added_permissions=}")
				embed = embed.add_field(
					name = "Permissions added",
					value = "\n".join(added_permissions)
				)
			if removed_permissions:
				logger.debug(f"{removed_permissions=}")
				embed = embed.add_field(
					name = "Permissions removed",
					value = "\n".join(removed_permissions)
				)

		if embed.description == "The following changes were made:\n":
			logger.debug(f"{hash(before)=}")
			logger.debug(f"{hash(after)=}")
			attrs = [f for f in dir(after) if not f.startswith('_') and not callable(getattr(after,f))]
			for attr in attrs:
				logger.debug(f"Comparing {attr} in before/after")
				value_before = getattr(before, attr)
				value_after = getattr(after, attr)
				logger.debug(f"{value_before=}")
				logger.debug(f"{value_after=}")
				if value_before != value_after:
					logger.warning(f"{attr} not equal")
				subattrs = [f for f in dir(getattr(before, attr)) if not f.startswith('_') and not callable(getattr(getattr(before, attr),f))]
				for subattr in subattrs:
					logger.debug(f"Comparing {attr}.{subattr} in before/after")
					value_before = getattr(before, attr)
					if value_before:
						value_before = getattr(value_before, subattr)
					value_after = getattr(after, attr)
					if value_after:
						value_after = getattr(value_after, subattr)
					logger.debug(f"{value_before=}")
					logger.debug(f"{value_after=}")
					if value_before != value_after:
						logger.warning(f"{attr}.{subattr} not equal")
			logger.warning("on_guild_role_update not handled\n")
			return

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_guild_role_update sent to channel\n")

	# EMOJIS AND STICKERS =======================================================

	@Cog.listener()
	async def on_guild_emojis_update(
		self,
		guild: discord.Guild,
		before: list[discord.Emoji],
		after: list[discord.Emoji]):
		"""Log added or removed emojis"""
		logger.info("on_guild_emojis_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		embed = discord.Embed(
			title = "Emoji updated",
			description = "\n"
		)

		before_set = set(before)
		after_set = set(after)
		added = after_set - before_set
		removed = before_set - after_set

		if not added and not removed:
			logger.warning("No changed detected -- what happened?")
			return

		added_string = "Added:\n"
		removed_string = "Removed:\n"

		for emoji in added:
			tag = f"<:{emoji.name}:{emoji.id}>"
			added_string += f"{tag} - added by {emoji.user.display_name} ({emoji.user})\n"
		for emoji in removed:
			tag = f"<:{emoji.name}:{emoji.id}>"
			removed_string += f"{tag} - removed by {emoji.user.display_name} ({emoji.user})\n"
		if added:
			logger.debug(f"{added=}")
			embed.description += added_string
		if removed:
			logger.debug(f"{removed=}")
			embed.description += removed_string

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_guild_emojis_update sent to channel\n")

	@Cog.listener()
	async def on_guild_stickers_update(
		self,
		guild: discord.Guild,
		before: list[discord.Sticker],
		after: list[discord.Sticker]):
		"""Log added or removed stickers"""
		logger.info("on_guild_stickers_update received")
		logger.debug(f"{before=}")
		logger.debug(f"{after=}")
		embed = discord.Embed(
			title = "Stickers updated",
		)

		before_set = set(before)
		after_set = set(after)
		added = after_set - before_set
		removed = before_set - after_set

		if not added and not removed:
			logger.warning("No changed detected -- what happened?")
			return

		added_string = "Added:\n"
		removed_string = "Removed:\n"

		for sticker in added:
			added_string += f"- <:{sticker.name}:{sticker.id}> - {sticker.description}\n"
		for sticker in removed:
			removed_string += f"- <:{sticker.name}:{sticker.id}> - {sticker.description}\n"
		if added:
			logger.debug(f"{added=}")
			embed.description += added_string
		if removed:
			logger.debug(f"{removed=}")
			embed.description += removed_string

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_guild_stickers_update sent to channel\n")

	# INVITES ===================================================================

	@Cog.listener()
	async def on_invite_create(
		self,
		invite: discord.Invite):
		"""Log created invites"""
		logger.info("on_invite_create received")
		logger.debug(f"{invite=}")
		embed = discord.Embed(
			title = "Invite created",
			url = invite.url,
			colour = 0x00ff00,
		).set_author(
			name = f"{invite.inviter.display_name} ({invite.inviter})",
			icon_url = invite.inviter.display_avatar.url
		).add_field(
			name = "Channel",
			value = invite.channel.mention,
		).add_field(
			name = "Code",
			value = invite.code,
		).add_field(
			name = "Max uses",
			value = invite.max_uses
		).add_field(
			name = "Max age",
			value = str(timedelta(seconds = invite.max_age))
		).add_footer(
			text = "Invite " + invite.id
		)

		if invite.temporary:
			embed.description = "(Invite is temporary; anyone joining will be kicked after disconnect"

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_invite_create sent to channel\n")

	@Cog.listener()
	async def on_invite_delete(
		self,
		invite: discord.Invite):
		"""Log deleted invites"""
		logger.info("on_invite_delete received")
		logger.debug(f"{invite=}")
		embed = discord.Embed(
			title = "Invite deleted",
			url = invite.url,
			colour = 0xff0000,
		).set_author(
			name = f"{invite.inviter.display_name} ({invite.inviter})",
			icon_url = invite.inviter.display_avatar.url
		).add_field(
			name = "Channel",
			value = invite.channel.mention,
		).add_field(
			name = "Code",
			value = invite.code,
		).add_field(
			name = "Uses",
			value = invite.uses
		).add_field(
			name = "Created at",
			value = invite.created_at
		).add_footer(
			text = "Invite " + invite.id
		)

		msg = await self.channel.send(embed = embed)
		if msg:
			logger.info("on_invite_delete sent to channel\n")