import discord
from discord import app_commands
from discord.ext import commands
from database import get_guild_data, update_guild_data, log_activity


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, title, description, user_id=None):
        settings = get_guild_data(guild.id)
        channel_id = settings.get('log_channel_id')
        channel = guild.get_channel(int(channel_id)) if channel_id else None
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
            await channel.send(embed=embed)
        log_activity(guild.id, title, description, user_id)

    @commands.command(name='لوق')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def set_logs(self, ctx, channel: discord.TextChannel):
        update_guild_data(ctx.guild.id, log_channel_id=channel.id)
        await ctx.reply(f'✅ تم تحديد روم اللوق: {channel.mention}')

    @app_commands.command(name='logs', description='Set the log channel')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_logs_slash(self, interaction, channel: discord.TextChannel):
        update_guild_data(interaction.guild.id, log_channel_id=channel.id)
        await interaction.response.send_message(f'✅ تم تحديد روم اللوق: {channel.mention}')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(member.guild, '👋 Member Left', f'{member} غادر السيرفر.', member.id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(guild, '🔨 Member Banned', f'{user} تم حظره.', user.id)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild and not message.author.bot:
            text = message.content[:1500] if message.content else '[بدون نص]'
            await self.send_log(message.guild, '🗑️ Message Deleted', f'العضو: {message.author.mention}\nالقناة: {message.channel.mention}\nالنص: {text}', message.author.id)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild and not before.author.bot and before.content != after.content:
            await self.send_log(before.guild, '✏️ Message Edited', f'العضو: {before.author.mention}\nالقناة: {before.channel.mention}\nقبل: {before.content[:700]}\nبعد: {after.content[:700]}', before.author.id)


async def setup(bot):
    await bot.add_cog(Logs(bot))
