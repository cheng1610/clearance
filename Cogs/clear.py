import discord
from discord.ext import commands, tasks
import asyncio

auto_clear_channels = {}
ctx_map = {}

class ClearCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_task.start()

    def cog_unload(self):
        self.delete_task.cancel()

    @discord.slash_command(name="clear_channel", description="clear channel")
    async def clear_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(
            discord.SlashCommandOptionType.channel,
            description='type of channel',
            channel_types=[
                discord.ChannelType.text,
                discord.ChannelType.voice
            ]
        )  # type: ignore
    ):
        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)

        if not permiss.manage_channels:
            return await ctx.respond("you can't do it!", ephemeral=True)

        await ctx.respond(f"deleted channel `{channel}`!", ephemeral=True)
        await channel.delete()

    @discord.slash_command(name="clear_category", description="clear category")
    async def clear_category(
        self,
        ctx: discord.ApplicationContext,
        category: discord.Option(
            discord.SlashCommandOptionType.channel,
            description='type of channel',
            channel_types=[discord.ChannelType.category]
        )  # type: ignore
    ):
        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)

        if not permiss.manage_channels:
            return await ctx.respond("you can't do it!", ephemeral=True)

        await ctx.respond(f'deleted category `{category}`!', ephemeral=True)
        await category.delete()

    @discord.slash_command(name="clear_message", description="clear messages in current channel")
    async def clear_message(
        self,
        ctx: discord.ApplicationContext,
        count: discord.Option(int, "number of messages to delete")  # type: ignore
    ):
        await ctx.defer(ephemeral=True)

        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)

        if not permiss.manage_channels:
            return await ctx.followup.send("you can't do it!", ephemeral=True)

        channel = ctx.channel

        deleted = 0
        async for message in channel.history(limit=count):
            await message.delete()
            deleted += 1

        await ctx.followup.send(f'deleted {deleted} messages in `{channel.name}`', ephemeral=True)

    @discord.slash_command(name="clear_user_message", description="clear user's message(s)")
    async def clear_user_message(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.User, "target user"),  # type: ignore
        message: discord.Option(str, "text to match", required=False),  # type: ignore
        limit: int = 200
    ):
        await ctx.defer(ephemeral=True)

        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)
        if not permiss.manage_channels:
            return await ctx.respond("you can't do it!", ephemeral=True)

        channel = ctx.channel
        count = 0

        async for msg in channel.history(limit=limit):
            if msg.author == user and (not message or message in msg.content):
                await msg.delete()
                count += 1

        await ctx.followup.send(f'deleted {count} messages from `{user}` in `{channel.name}`', ephemeral=True)

    @discord.slash_command(name="autoclear", description="auto clear messages periodically")
    async def autoclear(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(
            discord.SlashCommandOptionType.channel,
            description='target channel',
            channel_types=[discord.ChannelType.text, discord.ChannelType.voice]
        ),  # type: ignore
        time: discord.Option(int)  # type: ignore
    ):
        await ctx.defer(ephemeral=True)

        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)
        if not permiss.manage_channels:
            return await ctx.respond("you can't do it!", ephemeral=True)

        if time < 5:
            return await ctx.respond("please set at least 5 seconds.", ephemeral=True)

        auto_clear_channels[channel.id] = time
        ctx_map[channel.id] = ctx

        await ctx.respond(f"set to {channel.mention}, automatically delete messages every `{time} seconds`", ephemeral=True)

    @tasks.loop(seconds=5)
    async def delete_task(self):
        for channel_id, interval in list(auto_clear_channels.items()):
            channel = self.bot.get_channel(channel_id)
            ctx: discord.ApplicationContext = ctx_map.get(channel_id)

            if not channel:
                continue

            await asyncio.sleep(interval)

            try:
                async for msg in channel.history(limit=20):
                    await msg.delete()
            except discord.Forbidden:
                if ctx:
                    await ctx.respond(f"cannot delete in {channel.mention}, insufficient permissions", ephemeral=True)
            except Exception as e:
                if ctx:
                    await ctx.respond(f"error: {e}", ephemeral=True)

    @discord.slash_command(name="clear_role", description="clear role(s)")
    async def clear_role(
        self,
        ctx: discord.ApplicationContext,
        role: discord.Option(discord.Role, "role to delete")  # type: ignore
    ):
        await ctx.defer(ephemeral=True)

        permiss: discord.Permissions = ctx.channel.permissions_for(ctx.interaction.user)
        if not permiss.manage_channels:
            return await ctx.respond("you can't do it!", ephemeral=True)

        await role.delete()
        await ctx.respond('deleted!', ephemeral=True)

def setup(bot):
    bot.add_cog(ClearCog(bot))
