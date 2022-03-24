import discord
from discord.ext.commands import Cog
from os import getenv
from datetime import timedelta

def setup(bot):
	bot.add_cog(Audit(bot))

class Audit(Cog):
	"""Posts events from the audit log to a specified channel."""

	CHANNEL = 519071523714367489
	CHANNEL = 951378341162807387
	GUILD = int(getenv("GUILD_ID"))

	def __init__(self, bot):
		self.bot = bot
		self.channel = self.bot.get_channel(Audit.CHANNEL)
		self.guild = self.bot.get_guild(Audit.GUILD)
		print("Initialized Audit cog")

	@Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		self.channel = self.bot.get_channel(Audit.CHANNEL)
		self.guild = self.bot.get_guild(Audit.GUILD)

	# MESSAGES ==================================================================

	@Cog.listener()
	async def on_message_delete(self, message):
		"""Log deleted messages (if in cache)"""
		if message.author.id in set(
			[
				647368715742216193, # SaucyBot
	 			self.bot.user.id,
			]
		):
			return # ignore deleted messages from the above members

		await self.channel.send(
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
	async def on_message_edit(self, before, after):
		"""Log edited and updated messages (if in cache)"""

		if after.author.id == 823849032908668998: # SocialFeeds#0000
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

		if before.content != after.content: # content changed
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
			return await self.channel.send(embed=embed)

		if before.embeds != after.embeds and before.embeds: # embeds removed
			embed.description = "Embed was removed"
			embed = embed.add_field(
				name = "Content",
				value = after.content if after.content else "[No content]",
			)
			return await self.channel.send(embed=embed)
			

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
	async def on_guild_channel_create(self, channel):
		"""Log created channels"""
		url = f"https://discord.com/channels/{channel.guild.id}/{channel.id}"

		await self.channel.send(
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

	@Cog.listener()
	async def on_guild_channel_delete(self, channel):
		"""Log deleted channels"""
		await self.channel.send(
			embed = discord.Embed(
				title = "Channel deleted",
				colour = 0xff0000,
			).set_author(
				name = f"#{channel.name}",
			).set_footer(
				text = f"The channel {channel.id} was deleted",
			)
		)

	@Cog.listener()
	async def on_guild_channel_update(self, before, after):
		"""Log updated channels"""
		if after.id == 857144133742493736: # minecraft channel
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
			embed.description += f"- Channel name changed from `{before.name}` to `{after.name}`\n"
			embed.set_author(
				name = f"#{before.name} -> {after.name}"
			)

		if before.category_id != after.category_id:
			embed.description += f"- {after.mention} changed category from {before.category} to {after.category}\n"
		
		if before.changed_roles != after.changed_roles:
			embed.description += f"- {after.mention} changed roles from {before.changed_roles} to {after.changed_roles}\n"

		if before.default_auto_archive_duration != after.default_auto_archive_duration:
			embed.description += f"- {after.mention} changed auto-archive duration from {before.default_auto_archive_duration} minutes to {after.default_auto_archive_duration} minutes\n"

		if before.members != after.members:
			embed.description += f"- {after.mention} changed members from {before.members} to {after.members}\n"

		if after.nsfw and not before.nsfw:
			embed.description += f"- {after.mention} was marked as NSFW\n"
		if before.nsfw and not after.nsfw:
			embed.description += f"- {after.mention} was unmarked as NSFW\n"

		if before.overwrites != after.overwrites:
			embed.description += f"- {after.mention} changed overwrites from {before.overwrites} to {after.overwrites}\n"

		if after.permissions_synced and not before.permissions_synced:
			embed.description += f"- Permissions for {after.mention} were synced with {after.category}\n"
		if before.permissions_synced and not after.permissions_synced:
			embed.description += f"- Permissions for {after.mention} were unsynced with {after.category}\n"

		if before.slowmode_delay != after.slowmode_delay:
			embed.description += f"- Slowmode delay for {after.mention} was changed from {before.slowmode_delay} seconds to {after.slowmode_delay} seconds\n"

		if before.topic != after.topic:
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

		if before.type != after.type:
			embed.description = f"- The channel type of {after.mention} was changed from {before.type} to {after.type}\n"

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

		await self.channel.send(
			embed = embed
		)

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
	async def on_integration_create(self, integration):
		"""Log created integrations"""
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

		await self.channel.send(
			embed = embed
		)

	@Cog.listener()
	async def on_integration_update(self, integration):
		"""Log updated integrations""" # when is this actually called???
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

		await self.channel.send(
			embed = embed
		)

	@Cog.listener()
	async def on_raw_integration_delete(self, payload):
		"""Log deleted integrations"""
		user = await self.bot.fetch_user(payload.application_id)
		await self.channel.send(
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
	async def on_member_update(self, before, after):
		"""Log updated members (nicknames, roles, timeouts, permissions)"""
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
			embed.description = f"{after.mention} had their nickname changed"
			embed = embed.add_field(
				name = "Before",
				value = before.nick,
			).add_field(
				name = "After",
				value = after.nick,
			)
			return await self.channel.send(embed = embed)
		
		if before.roles != after.roles: # tested working
			before_roles = set(before.roles)
			after_roles = set(after.roles)
			added_roles = list(after_roles - before_roles)
			removed_roles = list(before_roles - after_roles)
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
			return await self.channel.send(embed = embed)

		if before.name != after.name or before.discriminator != after.discriminator:
			embed.description = f"{after.mention} changed their handle"
			embed = embed.add_field(
				name = "Before",
				value = before,
			).add_field(
				name = "After",
				value = after,
			)
			return await self.channel.send(embed = embed)

		if before.display_avatar != after.display_avatar:
			embed.description = f"{after.mention} changed their avatar"
			embed = embed.add_field(
				name = "Before",
				value = before.display_avatar.url,
			).add_field(
				name = "After",
				value = after.display_avatar.url,
			)
			return await self.channel.send(embed = embed)

		if after.timed_out and not before.timed_out: # idk how to time out people
			embed.description = f"{after.mention} is now timed out"
			return await self.channel.send(embed = embed)
			
		elif before.timed_out and not after.timed_out:
			embed.description = f"{after.mention} is no longer timed out"
			return await self.channel.send(embed = embed)

		elif before.communication_disabled_until != after.communication_disabled_until:
			embed.description = f"{after.mention} had their timeout duration changed"
			embed = embed.add_field(
				name = "Before",
				value = before.communication_disabled_until,
			).add_field(
				name = "After",
				value = after.communication_disabled_until,
			)
			return await self.channel.send(embed = embed)

		if before.guild_permissions != after.guild_permissions: # when?
			changed_permissions = []
			for b, a in zip(before.guild_permissions, after.guild_permissions):
				if b != a:
					changed_permissions.append((b[0], b[1], a[1]))
			added_permissions = []
			removed_permissions = []
			for p in changed_permissions:
				perm, value_before, value_after = p
				if value_after and not value_before:
					added_permissions.append(perm)
				elif value_before and not value_after:
					removed_permissions.append(perm)
			if added_permissions or removed_permissions:
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
			return await self.channel.send(embed = embed)

	# ROLES =====================================================================

	@Cog.listener()
	async def on_guild_role_create(self, role):
		"""Log created roles"""
		await self.channel.send(
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

	@Cog.listener()
	async def on_guild_role_delete(self, role):
		"""Log deleted roles"""
		await self.channel.send(
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

	@Cog.listener()
	async def on_guild_role_update(self, before, after):
		"""Log updated roles"""
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
			embed.description = f"- {after.mention} was renamed"
			embed = embed.add_field(
				name = "Before",
				value = before.name,
			).add_field(
				name = "After",
				value = after.name,
			)

		if before.colour != after.colour:
			embed.description = f"- {after.mention} had its colour changed from {before.colour} to {after.colour}\n"
		if after.hoist and not before.hoist:
			embed.description = f"- {after.mention} was hoisted; it will now show above online users\n"
		elif before.hoist and not after.hoist:
			embed.description = f"- {after.mention} was unhoisted; it will no longer show above online users\n"

		if before.permissions != after.permissions: # when an integration is updated, e.g.
			changed_permissions = []
			for b, a in zip(before.permissions, after.permissions):
				if b != a:
					changed_permissions.append((b[0], b[1], a[1]))
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
				embed = embed.add_field(
					name = "Permissions added",
					value = "\n".join(added_permissions)
				)
			if removed_permissions:
				embed = embed.add_field(
					name = "Permissions removed",
					value = "\n".join(removed_permissions)
				)
			return await self.channel.send(embed = embed)

		await self.channel.send(
			embed = embed
		)

	# EMOJIS AND STICKERS =======================================================

	@Cog.listener()
	async def on_guild_emojis_update(self, guild, before, after):
		"""Log added or removed emojis"""
		embed = discord.Embed(
			title = "Emoji updated",
			description = "\n"
		)

		before_set = set(before)
		after_set = set(after)
		added = after - before
		removed = before - after

		added_string = "Added:\n"
		removed_string = "Removed:\n"

		for emoji in added:
			tag = f"<:{emoji.name}:{emoji.id}>"
			added_string += f"{tag} - added by {emoji.user.display_name} ({emoji.user})\n"
		for emoji in removed:
			tag = f"<:{emoji.name}:{emoji.id}>"
			removed_string += f"{tag} - removed by {emoji.user.display_name} ({emoji.user})\n"
		if added:
			embed.description += added_string
		if removed:
			embed.description += removed_string

		await self.channel.send(embed = embed)

	@Cog.listener()
	async def on_guild_stickers_update(self, guild, before, after):
		"""Log added or removed stickers"""
		embed = discord.Embed(
			title = "Stickers updated",
		)

		before_set = set(before)
		after_set = set(after)
		added = after - before
		removed = before - after

		added_string = "Added:\n"
		removed_string = "Removed:\n"

		for sticker in added:
			added_string += f"- <:{sticker.name}:{sticker.id}> - {sticker.description}\n"
		for sticker in removed:
			removed_string += f"- <:{sticker.name}:{sticker.id}> - {sticker.description}\n"
		if added:
			embed.description += added_string
		if removed:
			embed.description += removed_string

		await self.channel.send(embed = embed)

	# INVITES ===================================================================

	@Cog.listener()
	async def on_invite_create(self, invite):
		"""Log created invites"""
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

		await self.channel.send(embed = embed)

	@Cog.listener()
	async def on_invite_delete(self, invite):
		"""Log deleted invites"""
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

		await self.channel.send(embed = embed)