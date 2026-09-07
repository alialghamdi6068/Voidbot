import discord
from discord.ext import commands
from config import BOT_NAME


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='حالة')
    @commands.is_owner()
    async def status(self, ctx):
        await ctx.reply(f'🔥 {BOT_NAME} يعمل.\nالسيرفرات: **{len(self.bot.guilds)}**\nPing: **{round(self.bot.latency * 1000)}ms**')

    @commands.command(name='مزامنة')
    @commands.is_owner()
    async def sync(self, ctx):
        synced = await self.bot.tree.sync()
        await ctx.reply(f'✅ تمت مزامنة **{len(synced)}** أمر Slash.')


async def setup(bot):
    await bot.add_cog(Owner(bot))
