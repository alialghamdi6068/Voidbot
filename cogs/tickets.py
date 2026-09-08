import discord
from discord.ext import commands
from database import get_guild_data, connection, log_activity


class TicketView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label='استلام', style=discord.ButtonStyle.primary, emoji='📥', custom_id='flame_ticket_claim')
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message('❌ هذا الزر للإدارة فقط.', ephemeral=True)
        await interaction.response.send_message(f'📥 تم استلام التذكرة بواسطة {interaction.user.mention}.')

    @discord.ui.button(label='إغلاق', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='flame_ticket_close')
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return
        with connection() as conn:
            row = conn.execute('SELECT * FROM tickets WHERE channel_id=? AND status="open"', (interaction.channel.id,)).fetchone()
            if not row:
                return await interaction.response.send_message('❌ هذه التذكرة مغلقة أو غير موجودة.', ephemeral=True)
            if interaction.user.id != row['user_id'] and not interaction.user.guild_permissions.manage_channels:
                return await interaction.response.send_message('❌ ما عندك صلاحية إغلاق هذه التذكرة.', ephemeral=True)
            conn.execute("UPDATE tickets SET status='closed', closed_at=CURRENT_TIMESTAMP WHERE channel_id=?", (interaction.channel.id,))
        log_activity(interaction.guild.id, 'ticket_close', str(interaction.channel), interaction.user.id)
        await interaction.response.send_message('🔒 سيتم إغلاق التذكرة.')
        await interaction.channel.delete(reason=f'Ticket closed by {interaction.user}')


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def ticket_overwrites(self, guild, user):
        settings = get_guild_data(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }
        role_id = settings.get('ticket_support_role_id')
        if role_id:
            role = guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        return overwrites

    async def create_ticket(self, interaction):
        guild, user = interaction.guild, interaction.user
        settings = get_guild_data(guild.id)
        category = guild.get_channel(int(settings['ticket_category_id'])) if settings.get('ticket_category_id') else None
        category = category if isinstance(category, discord.CategoryChannel) else None
        existing = discord.utils.find(lambda c: c.name == f'ticket-{user.id}', guild.text_channels)
        if existing:
            return await interaction.response.send_message(f'❌ عندك تذكرة مفتوحة بالفعل: {existing.mention}', ephemeral=True)
        channel = await guild.create_text_channel(f'ticket-{user.id}', category=category, overwrites=self.ticket_overwrites(guild, user), reason='Flame ticket')
        with connection() as conn:
            conn.execute('INSERT INTO tickets(guild_id,channel_id,user_id) VALUES(?,?,?)', (guild.id, channel.id, user.id))
        log_activity(guild.id, 'ticket_open', str(channel), user.id)
        embed = discord.Embed(title='🎫 تذكرة دعم', description=f'{user.mention} أهلاً بك! اكتب تفاصيل طلبك هنا.\n\nفريق الدعم يستطيع استلام التذكرة وإغلاقها.', color=discord.Color.blurple())
        await channel.send(content=user.mention, embed=embed, view=TicketView(self))
        await interaction.response.send_message(f'✅ تم فتح تذكرتك: {channel.mention}', ephemeral=True)

    @commands.command(name='تكت')
    @commands.guild_only()
    async def ticket_prefix(self, ctx):
        guild, user = ctx.guild, ctx.author
        settings = get_guild_data(guild.id)
        category = guild.get_channel(int(settings['ticket_category_id'])) if settings.get('ticket_category_id') else None
        category = category if isinstance(category, discord.CategoryChannel) else None
        existing = discord.utils.find(lambda c: c.name == f'ticket-{user.id}', guild.text_channels)
        if existing:
            return await ctx.reply(f'❌ عندك تذكرة مفتوحة بالفعل: {existing.mention}')
        channel = await guild.create_text_channel(f'ticket-{user.id}', category=category, overwrites=self.ticket_overwrites(guild, user), reason='Flame ticket')
        with connection() as conn:
            conn.execute('INSERT INTO tickets(guild_id,channel_id,user_id) VALUES(?,?,?)', (guild.id, channel.id, user.id))
        await channel.send(content=user.mention, embed=discord.Embed(title='🎫 تذكرة دعم', description='اكتب تفاصيل طلبك هنا.', color=discord.Color.blurple()), view=TicketView(self))
        log_activity(guild.id, 'ticket_open', str(channel), user.id)
        await ctx.reply(f'✅ تم فتح تذكرتك: {channel.mention}')

    @commands.command(name='استلام')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def claim_prefix(self, ctx):
        await ctx.reply(f'📥 تم استلام التذكرة بواسطة {ctx.author.mention}.')

    @commands.command(name='اغلاق')
    @commands.guild_only()
    async def close_prefix(self, ctx):
        with connection() as conn:
            row = conn.execute('SELECT user_id FROM tickets WHERE channel_id=? AND status="open"', (ctx.channel.id,)).fetchone()
            if not row:
                return await ctx.reply('❌ هذا الروم ليس تذكرة مفتوحة.')
            if ctx.author.id != row['user_id'] and not ctx.author.guild_permissions.manage_channels:
                return await ctx.reply('❌ ما تقدر تغلق هذه التذكرة.')
            conn.execute("UPDATE tickets SET status='closed', closed_at=CURRENT_TIMESTAMP WHERE channel_id=?", (ctx.channel.id,))
        await ctx.reply('🔒 سيتم إغلاق التذكرة.')
        await ctx.channel.delete(reason=f'Ticket closed by {ctx.author}')

    @commands.command(name='اضافة')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def add_prefix(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
        await ctx.reply(f'✅ تمت إضافة {member.mention} للتذكرة.')

    @commands.command(name='ازالة')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def remove_prefix(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.reply(f'✅ تمت إزالة {member.mention} من التذكرة.')

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, '_flame_ticket_view_added', False):
            self.bot.add_view(TicketView(self))
            self.bot._flame_ticket_view_added = True


async def setup(bot):
    await bot.add_cog(Tickets(bot))
