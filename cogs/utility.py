import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_NAME


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='اوامر', aliases=['مساعدة', 'help'])
    @commands.guild_only()
    async def all_commands(self, ctx):
        groups = {}
        for command in self.bot.commands:
            if command.hidden or command.name in groups:
                continue
            cog_name = command.cog_name or 'أخرى'
            groups.setdefault(cog_name, []).append(command)

        embed = discord.Embed(
            title=f'🔥 {BOT_NAME} — جميع الأوامر',
            description='هذه قائمة الأوامر المتاحة للبوت. الأوامر التي تحتاج صلاحيات لن تعمل إلا للمصرح لهم.',
            color=discord.Color.blurple()
        )
        for cog_name, commands_list in groups.items():
            names = []
            for command in commands_list:
                names.append(f'`!{command.name}`')
            embed.add_field(name=f'📂 {cog_name}', value=' '.join(names)[:1024] or 'لا توجد أوامر', inline=False)

        embed.set_footer(text=f'{BOT_NAME} • استخدم /help أيضاً للأوامر السلاش')
        await ctx.reply(embed=embed)

    @app_commands.command(name='help', description='Show all Flame commands')
    async def help_slash(self, interaction):
        groups = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
            cog_name = command.cog_name or 'Other'
            groups.setdefault(cog_name, []).append(command.name)
        embed = discord.Embed(title=f'🔥 {BOT_NAME} — جميع الأوامر', color=discord.Color.blurple())
        for cog_name, names in groups.items():
            embed.add_field(name=f'📂 {cog_name}', value=' '.join(f'`!{n}`' for n in names)[:1024], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name='بينج')
    async def ping(self, ctx):
        await ctx.reply(f'🏓 Pong! `{round(self.bot.latency * 1000)}ms`')

    @app_commands.command(name='ping', description='Show bot latency')
    async def ping_slash(self, interaction):
        await interaction.response.send_message(f'🏓 Pong! `{round(self.bot.latency * 1000)}ms`')


async def setup(bot):
    await bot.add_cog(Utility(bot))
