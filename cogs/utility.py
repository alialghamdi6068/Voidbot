import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_NAME


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='مساعدة')
    @commands.guild_only()
    async def help_prefix(self, ctx):
        embed = discord.Embed(title=f'🔥 {BOT_NAME} — المساعدة', description='استخدم الأوامر التالية:', color=discord.Color.blurple())
        embed.add_field(name='🛡️ إدارة', value='`!باند` `!طرد` `!تايم` `!تحذير` `!تحذيرات` `!مسح` `!قفل` `!فتح`', inline=False)
        embed.add_field(name='🎫 أنظمة', value='`!تكت` `!تقديم` `!اقتراح` `!قيفاواي` `!غياب` `!لفل` `!توب`', inline=False)
        embed.add_field(name='⏰ أدوات', value='`!تذكير` `!جدولة` `!رد`', inline=False)
        await ctx.reply(embed=embed)

    @app_commands.command(name='help', description='Show Flame commands')
    async def help_slash(self, interaction):
        await interaction.response.send_message('🔥 استخدم `!مساعدة` لعرض أوامر Flame الأساسية.', ephemeral=True)

    @commands.command(name='بينج')
    async def ping(self, ctx):
        await ctx.reply(f'🏓 Pong! `{round(self.bot.latency * 1000)}ms`')

    @app_commands.command(name='ping', description='Show bot latency')
    async def ping_slash(self, interaction):
        await interaction.response.send_message(f'🏓 Pong! `{round(self.bot.latency * 1000)}ms`')


async def setup(bot):
    await bot.add_cog(Utility(bot))
