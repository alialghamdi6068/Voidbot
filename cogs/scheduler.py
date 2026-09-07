import re
import time
import discord
from discord import app_commands
from discord.ext import commands, tasks
from database import connection, log_activity

DURATION_RE = re.compile(r'^(\d+)([smhd])$', re.I)


def seconds(value):
    m = DURATION_RE.fullmatch(value.strip())
    if not m:
        raise ValueError
    return int(m.group(1)) * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[m.group(2).lower()]


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    @tasks.loop(seconds=5)
    async def loop(self):
        with connection() as conn:
            rows = conn.execute('SELECT * FROM schedules WHERE sent=0 AND due_at<=?', (time.time(),)).fetchall()
            for row in rows:
                conn.execute('UPDATE schedules SET sent=1 WHERE id=?', (row['id'],))
        for row in rows:
            channel = self.bot.get_channel(row['channel_id'])
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(row['text'])
                except discord.HTTPException:
                    pass

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @commands.command(name='جدولة')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def schedule(self, ctx, duration: str, *, text: str):
        try:
            delay = seconds(duration)
        except ValueError:
            return await ctx.reply('❌ استخدم مدة مثل `10m` أو `2h` أو `1d`.')
        if delay < 5 or delay > 30 * 86400:
            return await ctx.reply('❌ المدة يجب أن تكون بين 5 ثوانٍ و30 يوم.')
        with connection() as conn:
            conn.execute('INSERT INTO schedules(guild_id,channel_id,text,due_at) VALUES(?,?,?,?)', (ctx.guild.id, ctx.channel.id, text[:2000], time.time() + delay))
        log_activity(ctx.guild.id, 'schedule_create', text[:200], ctx.author.id)
        await ctx.reply('✅ تمت جدولة الرسالة.')

    @app_commands.command(name='schedule', description='Schedule a message')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_slash(self, interaction, duration: str, text: str):
        try:
            delay = seconds(duration)
        except ValueError:
            return await interaction.response.send_message('❌ استخدم 10m أو 2h أو 1d.', ephemeral=True)
        if delay < 5 or delay > 30 * 86400:
            return await interaction.response.send_message('❌ المدة يجب أن تكون بين 5 ثوانٍ و30 يوم.', ephemeral=True)
        with connection() as conn:
            conn.execute('INSERT INTO schedules(guild_id,channel_id,text,due_at) VALUES(?,?,?,?)', (interaction.guild.id, interaction.channel.id, text[:2000], time.time() + delay))
        await interaction.response.send_message('✅ تمت جدولة الرسالة.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scheduler(bot))
