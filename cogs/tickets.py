import discord
from discord.ext import commands
from database import get_guild_data, connection, log_activity


class TicketPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label='فتح تذكرة', style=discord.ButtonStyle.success, emoji='🎫', custom_id='flame_ticket_open')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.create_ticket(interaction)


class TicketView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label='استلام', style=discord.ButtonStyle.primary, emoji='📥', custom_id='flame_ticket_claim')
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message('❌ هذا الزر للإدارة فقط.', ephemeral=True)
        await interaction.response.send_message(f'📥 تم استلام التذكرة بواسطة {interaction.user.mention}.')
        log_activity(interaction.guild.id, 'ticket_claim', str(interaction.channel), interaction.user.id)

    @discord.ui.button(label='إغلاق', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='flame_ticket_close')
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.channel:
            return
        with connection() as conn:
            row = conn.execute('SELECT * FROM tickets WHERE channel_id=? AND status="open"', (interaction.channel.id,)).fetchone()
            if not row:
                return await interaction.response.send_message('❌ هذه التذكرة مغلقة أو غير موجودة.', ephemeral=True)
            if interaction.user.id != row['user_id'] and not interaction.user.guild_permissions.manage_channels:
                return await interaction.response.send_message('❌ ما عندك صلاحية إغلاق هذه التذكرة.', ephemeral=True)
            conn.execute("UPDATE tickets SET status='closed', closed_at=CURRENT_TIMESTAMP WHERE channel_id=?", (interaction.channel.id,))
        await self.cog.write_ticket_log(interaction.guild, f'🔒 تم إغلاق `{interaction.channel.name}` بواسطة {interaction.user.mention}.')
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
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True, read_message_history=True)
        role_id = settings.get('ticket_support_role_id')
        if role_id:
            role = guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        return overwrites

    async def write_ticket_log(self, guild, text):
        settings = get_guild_data(guild.id)
        channel_id = settings.get('ticket_log_channel_id')
        if not channel_id:
            return
        channel = guild.get_channel(int(channel_id))
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(text)
            except discord.HTTPException:
                pass

    async def create_ticket(self, interaction):
        guild, user = interaction.guild, interaction.user
        if not guild:
            return await interaction.response.send_message('❌ هذا الزر يعمل داخل السيرفر فقط.', ephemeral=True)

        settings = get_guild_data(guild.id)
        category = guild.get_channel(int(settings['ticket_category_id'])) if settings.get('ticket_category_id') else None
        category = category if isinstance(category, discord.CategoryChannel) else None

        existing = discord.utils.find(lambda c: c.topic == f'flame-ticket-user:{user.id}', guild.text_channels)
        if existing:
            return await interaction.response.send_message(f'❌ عندك تذكرة مفتوحة بالفعل: {existing.mention}', ephemeral=True)

        # نحصل على رقم متسلسل من قاعدة البيانات قبل إنشاء الروم.
        with connection() as conn:
            cursor = conn.execute('INSERT INTO tickets(guild_id,channel_id,user_id) VALUES(?,?,?)', (guild.id, 0, user.id))
            ticket_id = cursor.lastrowid

        try:
            channel = await guild.create_text_channel(
                f'ticket-{ticket_id:04d}',
                category=category,
                overwrites=self.ticket_overwrites(guild, user),
                topic=f'flame-ticket-user:{user.id}',
                reason='Flame ticket'
            )
            with connection() as conn:
                conn.execute('UPDATE tickets SET channel_id=? WHERE id=?', (channel.id, ticket_id))
        except discord.Forbidden:
            with connection() as conn:
                conn.execute('DELETE FROM tickets WHERE id=?', (ticket_id,))
            return await interaction.response.send_message('❌ البوت لا يملك Manage Channels لإنشاء التذكرة.', ephemeral=True)
        except discord.HTTPException:
            with connection() as conn:
                conn.execute('DELETE FROM tickets WHERE id=?', (ticket_id,))
            return await interaction.response.send_message('❌ تعذر إنشاء التذكرة.', ephemeral=True)

        log_activity(guild.id, 'ticket_open', str(channel), user.id)
        await self.write_ticket_log(guild, f'🎫 تم فتح `{channel.name}` بواسطة {user.mention}.')

        embed = discord.Embed(
            title=f'🎫 تذكرة دعم #{ticket_id:04d}',
            description=(f'{user.mention} أهلاً بك!\n\n'
                         'اكتب تفاصيل طلبك هنا وسيقوم فريق الدعم بمساعدتك.\n\n'
                         '📥 **استلام** — لفريق الدعم\n'
                         '🔒 **إغلاق** — لإغلاق التذكرة.'),
            color=discord.Color.blurple()
        )
        await channel.send(content=user.mention, embed=embed, view=TicketView(self))
        await interaction.response.send_message(f'✅ تم فتح تذكرتك: {channel.mention}', ephemeral=True)

    async def send_panel(self, ctx):
        settings = get_guild_data(ctx.guild.id)
        panel_id = settings.get('ticket_panel_channel_id')
        channel = ctx.guild.get_channel(int(panel_id)) if panel_id else None
        if not isinstance(channel, discord.TextChannel):
            return await ctx.reply('❌ حدد **روم لوحة التذاكر** من الموقع أولاً، ثم استخدم `!تكت`.')

        embed = discord.Embed(
            title='🎫 نظام التذاكر',
            description='تحتاج مساعدة؟ اضغط **🎫 فتح تذكرة** بالأسفل وسيتم فتح تذكرة خاصة بك.',
            color=discord.Color.blurple()
        )
        embed.set_footer(text='Flame • Ticket System')
        await channel.send(embed=embed, view=TicketPanelView(self))
        await ctx.reply(f'✅ تم إرسال لوحة التذاكر في {channel.mention}.')

    @commands.command(name='تكت')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def ticket_panel(self, ctx):
        await self.send_panel(ctx)

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
        await self.write_ticket_log(ctx.guild, f'🔒 تم إغلاق `{ctx.channel.name}` بواسطة {ctx.author.mention}.')
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
        if not getattr(self.bot, '_flame_ticket_views_added', False):
            self.bot.add_view(TicketPanelView(self))
            self.bot.add_view(TicketView(self))
            self.bot._flame_ticket_views_added = True


async def setup(bot):
    await bot.add_cog(Tickets(bot))
