import discord
from discord import app_commands
from discord.ext import commands
from database import connection, get_guild_data, update_guild_data, log_activity


class SuggestionView(discord.ui.View):
    def __init__(self, cog, suggestion_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.suggestion_id = suggestion_id

    @discord.ui.button(label='👍 0', style=discord.ButtonStyle.success, custom_id='flame_suggestion_up')
    async def up(self, interaction, button):
        await self.cog.vote(interaction, self.suggestion_id, True, button)

    @discord.ui.button(label='👎 0', style=discord.ButtonStyle.danger, custom_id='flame_suggestion_down')
    async def down(self, interaction, button):
        await self.cog.vote(interaction, self.suggestion_id, False, button)

    @discord.ui.button(label='قبول', style=discord.ButtonStyle.primary, custom_id='flame_suggestion_accept')
    async def accept(self, interaction, button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message('❌ هذا الزر للإدارة فقط.', ephemeral=True)
        with connection() as conn:
            conn.execute('UPDATE suggestions SET status=? WHERE id=?', ('accepted', self.suggestion_id))
        await interaction.response.send_message('✅ تم قبول الاقتراح.', ephemeral=True)

    @discord.ui.button(label='رفض', style=discord.ButtonStyle.secondary, custom_id='flame_suggestion_reject')
    async def reject(self, interaction, button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message('❌ هذا الزر للإدارة فقط.', ephemeral=True)
        with connection() as conn:
            conn.execute('UPDATE suggestions SET status=? WHERE id=?', ('rejected', self.suggestion_id))
        await interaction.response.send_message('❌ تم رفض الاقتراح.', ephemeral=True)


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create(self, guild, user, content, channel):
        with connection() as conn:
            cur = conn.execute('INSERT INTO suggestions(guild_id,user_id,content) VALUES(?,?,?)', (guild.id, user.id, content))
            suggestion_id = cur.lastrowid
        embed = discord.Embed(title='💡 اقتراح جديد', description=content, color=discord.Color.blurple())
        embed.add_field(name='صاحب الاقتراح', value=user.mention)
        embed.add_field(name='الحالة', value='🟡 قيد المراجعة')
        msg = await channel.send(embed=embed, view=SuggestionView(self, suggestion_id))
        with connection() as conn:
            conn.execute('UPDATE suggestions SET message_id=? WHERE id=?', (msg.id, suggestion_id))
        log_activity(guild.id, 'suggestion', content, user.id)
        return msg

    async def vote(self, interaction, suggestion_id, up, button):
        message = interaction.message
        reactions = {str(r.emoji): r.count - (1 if self.bot.user in r.users else 0) for r in message.reactions}
        emoji = '👍' if up else '👎'
        await interaction.response.send_message(f'تم تسجيل تصويتك {emoji}', ephemeral=True)
        for child in interaction.message.components:
            pass

    @commands.command(name='اقتراح')
    @commands.guild_only()
    async def suggestion_prefix(self, ctx, *, content: str):
        settings = get_guild_data(ctx.guild.id)
        channel_id = settings.get('suggestions_channel_id')
        channel = ctx.guild.get_channel(int(channel_id)) if channel_id else ctx.channel
        if not isinstance(channel, discord.TextChannel):
            return await ctx.reply('❌ روم الاقتراحات غير صحيح.')
        await self.create(ctx.guild, ctx.author, content, channel)
        if channel.id != ctx.channel.id:
            await ctx.reply(f'✅ تم إرسال اقتراحك في {channel.mention}.')

    @app_commands.command(name='suggest', description='Send a suggestion')
    async def suggestion_slash(self, interaction, content: str):
        settings = get_guild_data(interaction.guild.id)
        channel_id = settings.get('suggestions_channel_id')
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message('❌ روم الاقتراحات غير صحيح.', ephemeral=True)
        await self.create(interaction.guild, interaction.user, content, channel)
        await interaction.response.send_message('✅ تم إرسال اقتراحك.', ephemeral=True)

    @commands.command(name='اقتراحات')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def configure(self, ctx, channel: discord.TextChannel):
        update_guild_data(ctx.guild.id, suggestions_channel_id=channel.id)
        await ctx.reply(f'✅ تم تحديد روم الاقتراحات: {channel.mention}')


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
