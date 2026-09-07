import discord
from discord import app_commands
from discord.ext import commands
from database import get_guild_data, log_activity


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = get_guild_data(member.guild.id)
        channel_id = settings.get('welcome_channel_id')
        if not channel_id:
            return
        channel = member.guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return
        message = settings.get('welcome_message', 'أهلاً وسهلاً {member} في **{server}**! 👋')
        message = message.replace('{member}', member.mention).replace('{server}', member.guild.name).replace('{count}', str(member.guild.member_count or 0))
        await channel.send(message)
        role_id = settings.get('auto_role_id')
        if role_id:
            role = member.guild.get_role(int(role_id))
            if role and role < member.guild.me.top_role:
                try:
                    await member.add_roles(role, reason='Flame auto role')
                except discord.HTTPException:
                    pass
        log_activity(member.guild.id, 'member_join', str(member), member.id)

    @commands.command(name='ترحيب')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def welcome_prefix(self, ctx, channel: discord.TextChannel, *, message: str = 'أهلاً وسهلاً {member} في **{server}**! 👋'):
        from database import update_guild_data
        update_guild_data(ctx.guild.id, welcome_channel_id=channel.id, welcome_message=message)
        await ctx.reply(f'✅ تم ضبط الترحيب في {channel.mention}.')

    @app_commands.command(name='welcome', description='Set the welcome channel and message')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_slash(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str = 'أهلاً وسهلاً {member} في **{server}**! 👋'):
        from database import update_guild_data
        update_guild_data(interaction.guild.id, welcome_channel_id=channel.id, welcome_message=message)
        await interaction.response.send_message(f'✅ تم ضبط الترحيب في {channel.mention}.')


async def setup(bot):
    await bot.add_cog(Welcome(bot))
