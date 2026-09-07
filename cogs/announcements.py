import discord
from discord import app_commands
from discord.ext import commands


class Announcements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='تنبيه')
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def announcement(self, ctx, *, text: str):
        embed = discord.Embed(title='📢 إعلان', description=text[:4000], color=discord.Color.blurple())
        embed.set_footer(text=f'بواسطة {ctx.author}')
        await ctx.send(embed=embed)

    @app_commands.command(name='announcement', description='Send an announcement')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announcement_slash(self, interaction, text: str):
        embed = discord.Embed(title='📢 إعلان', description=text[:4000], color=discord.Color.blurple())
        embed.set_footer(text=f'بواسطة {interaction.user}')
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message('✅ تم إرسال الإعلان.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Announcements(bot))
