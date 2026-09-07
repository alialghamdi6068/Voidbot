import time
import discord
from discord import app_commands
from discord.ext import commands
from database import connection, log_activity


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        with connection() as conn:
            own = conn.execute('SELECT reason FROM afk WHERE guild_id=? AND user_id=?', (message.guild.id, message.author.id)).fetchone()
            if own:
                conn.execute('DELETE FROM afk WHERE guild_id=? AND user_id=?', (message.guild.id, message.author.id))
                await message.channel.send(f'👋 رجعت يا {message.author.mention}! تم إلغاء حالة الغياب.', delete_after=5)
            for target in message.mentions[:5]:
                row = conn.execute('SELECT reason FROM afk WHERE guild_id=? AND user_id=?', (message.guild.id, target.id)).fetchone()
                if row:
                    await message.channel.send(f'💤 {target.mention} حالياً غائب: {row["reason"]}', delete_after=6)

    async def set_afk(self, guild, user, reason):
        with connection() as conn:
            conn.execute('INSERT INTO afk(guild_id,user_id,reason) VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET reason=excluded.reason,created_at=CURRENT_TIMESTAMP', (guild.id, user.id, reason))
        log_activity(guild.id, 'afk', reason, user.id)

    @commands.command(name='غياب', aliases=['afk'])
    @commands.guild_only()
    async def afk_prefix(self, ctx, *, reason='بدون سبب'):
        await self.set_afk(ctx.guild, ctx.author, reason[:500])
        await ctx.reply(f'💤 تم تفعيل الغياب لك.
**السبب:** {reason[:500]}')

    @app_commands.command(name='afk', description='Set your AFK status')
    async def afk_slash(self, interaction, reason='بدون سبب'):
        await self.set_afk(interaction.guild, interaction.user, reason[:500])
        await interaction.response.send_message(f'💤 تم تفعيل الغياب لك.\n**السبب:** {reason[:500]}')


async def setup(bot):
    await bot.add_cog(AFK(bot))
