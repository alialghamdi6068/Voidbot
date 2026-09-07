import discord
from discord import app_commands
from discord.ext import commands
from database import get_guild_data, connection, log_activity


class ApplicationModal(discord.ui.Modal, title='نموذج التقديم'):
    answer = discord.ui.TextInput(label='اكتب تقديمك', style=discord.TextStyle.paragraph, min_length=10, max_length=2000, placeholder='اكتب التفاصيل هنا...')

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = get_guild_data(guild.id)
        channel = guild.get_channel(int(settings['applications_channel_id'])) if settings.get('applications_channel_id') else None
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message('❌ الإدارة لم تحدد روم التقديمات من الداشبورد.', ephemeral=True)
        with connection() as conn:
            cur = conn.execute('INSERT INTO applications(guild_id,user_id,content) VALUES(?,?,?)', (guild.id, interaction.user.id, str(self.answer)))
            application_id = cur.lastrowid
        embed = discord.Embed(title=f'📨 تقديم جديد #{application_id}', description=str(self.answer), color=discord.Color.blurple())
        embed.add_field(name='المتقدم', value=interaction.user.mention)
        embed.set_footer(text='الحالة: قيد المراجعة')
        await channel.send(embed=embed)
        log_activity(guild.id, 'application_submit', f'#{application_id}', interaction.user.id)
        await interaction.response.send_message('✅ تم ارسال تقديمك يرجى انتظار رد الإدارة.', ephemeral=True)


class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='تقديم')
    @commands.guild_only()
    async def application_prefix(self, ctx):
        settings = get_guild_data(ctx.guild.id)
        channel = ctx.guild.get_channel(int(settings['applications_channel_id'])) if settings.get('applications_channel_id') else None
        if not isinstance(channel, discord.TextChannel):
            return await ctx.reply('❌ الإدارة لم تحدد روم التقديمات من الداشبورد.')
        view = discord.ui.View(timeout=300)
        button = discord.ui.Button(label='فتح التقديم', style=discord.ButtonStyle.success, emoji='📝')
        async def callback(interaction):
            await interaction.response.send_modal(ApplicationModal(self))
        button.callback = callback
        view.add_item(button)
        await ctx.reply('📝 اضغط الزر لفتح نموذج التقديم.', view=view)

    @app_commands.command(name='apply', description='Open the application form')
    async def application_slash(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationModal(self))


async def setup(bot):
    await bot.add_cog(Applications(bot))
