import discord
from discord.ext import commands

from database import connection, log_activity


class Multiword(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='فك_حظر')
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: str):
        try:
            uid = int(user_id.strip('<@!>'))
            await ctx.guild.unban(discord.Object(id=uid), reason=f'فك حظر بواسطة {ctx.author}')
        except ValueError:
            return await ctx.reply('❌ أرسل ID صحيح.')
        except discord.NotFound:
            return await ctx.reply('❌ هذا المستخدم غير محظور.')
        log_activity(ctx.guild.id, 'unban', str(uid), ctx.author.id)
        await ctx.reply(f'✅ تم فك الحظر عن `{uid}`.')

    @commands.command(name='ريست_لفل')
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def reset_level(self, ctx, target: str):
        if target.strip().lower() == 'الكل':
            with connection() as conn:
                conn.execute('DELETE FROM levels WHERE guild_id=?', (ctx.guild.id,))
            log_activity(ctx.guild.id, 'reset_all_levels', 'all members', ctx.author.id)
            return await ctx.reply('🔄 تم تصفير مستويات وXP جميع أعضاء السيرفر.')
        target = target.strip()
        if target.startswith('<@') and target.endswith('>'):
            target = target.replace('<@!', '').replace('<@', '').replace('>', '')
        try:
            member = ctx.guild.get_member(int(target))
        except ValueError:
            member = None
        if not member:
            try:
                member = await commands.MemberConverter().convert(ctx, target)
            except commands.BadArgument:
                return await ctx.reply('❌ استخدم منشن عضو أو اكتب `الكل`.')
        with connection() as conn:
            conn.execute('DELETE FROM levels WHERE guild_id=? AND user_id=?', (ctx.guild.id, member.id))
        log_activity(ctx.guild.id, 'reset_level', str(member), member.id)
        await ctx.reply(f'🔄 تم تصفير لفل وXP {member.mention}.')

    @commands.command(name='رتب_السيرفر')
    @commands.guild_only()
    async def server_roles(self, ctx):
        roles = [r.mention for r in reversed(ctx.guild.roles) if not r.is_default()]
        await ctx.reply(f'🏷️ **رتب السيرفر ({len(roles)})**\n' + (' '.join(roles)[:1900] if roles else 'لا توجد رتب.'))

    @commands.command(name='اعضاء_اونلاين')
    @commands.guild_only()
    async def online(self, ctx):
        count = sum(1 for m in ctx.guild.members if m.status != discord.Status.offline)
        await ctx.reply(f'🟢 الأعضاء المتصلون: **{count}** من **{ctx.guild.member_count or 0}**')

    @commands.command(name='احصائيات_السيرفر')
    @commands.guild_only()
    async def server_stats(self, ctx):
        g = ctx.guild
        await ctx.reply(f'📊 **{g.name}**\n👥 {g.member_count or 0} عضو\n🤖 {sum(m.bot for m in g.members)} بوت\n💬 {len(g.text_channels)} نصية\n🔊 {len(g.voice_channels)} صوتية\n🏷️ {len(g.roles)-1} رتبة')

    @commands.command(name='سجل_العضو')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def member_log(self, ctx, member: discord.Member):
        with connection() as conn:
            rows = conn.execute('SELECT action, details, created_at FROM activity WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 20', (ctx.guild.id, member.id)).fetchall()
        if not rows:
            return await ctx.reply('📝 لا يوجد سجل لهذا العضو.')
        lines = [f'`{r["created_at"]}` **{r["action"]}** — {r["details"][:100]}' for r in rows]
        await ctx.reply(f'📝 **سجل {member}**\n' + '\n'.join(lines)[:1900])

    @commands.command(name='عمر_الحساب')
    async def account_age(self, ctx, member: discord.Member | None = None):
        member = member or ctx.author
        days = (discord.utils.utcnow() - member.created_at).days
        await ctx.reply(f'👤 حساب {member.mention} عمره تقريبًا **{days} يوم**.')

    @commands.command(name='عمر_السيرفر')
    @commands.guild_only()
    async def server_age(self, ctx):
        days = (discord.utils.utcnow() - ctx.guild.created_at).days
        await ctx.reply(f'🏠 السيرفر عمره تقريبًا **{days} يوم**.')

    @commands.command(name='اختصار_الرابط')
    async def shorten(self, ctx, url: str):
        import requests
        if not url.startswith(('http://', 'https://')):
            return await ctx.reply('❌ أرسل رابطًا يبدأ بـ http:// أو https://')
        try:
            r = requests.get('https://is.gd/create.php', params={'format': 'simple', 'url': url}, timeout=8)
            short = r.text.strip()
            if r.ok and short.startswith('http'):
                return await ctx.reply(f'🔗 {short}')
        except requests.RequestException:
            pass
        await ctx.reply('❌ تعذر اختصار الرابط الآن.')

    @commands.command(name='وقت_عالمي')
    async def world_time(self, ctx, *, city: str):
        import requests
        zones = {'الرياض': 'Asia/Riyadh', 'جدة': 'Asia/Riyadh', 'دبي': 'Asia/Dubai', 'لندن': 'Europe/London', 'نيويورك': 'America/New_York', 'طوكيو': 'Asia/Tokyo'}
        zone = zones.get(city.strip(), city.strip())
        try:
            r = requests.get(f'https://worldtimeapi.org/api/timezone/{zone}', timeout=8)
            data = r.json()
            dt = data.get('datetime', '')[:19].replace('T', ' ')
            if dt:
                return await ctx.reply(f'🌍 الوقت في **{city}**: **{dt}**')
        except Exception:
            pass
        await ctx.reply('❌ المدينة غير مدعومة.')

    @commands.command(name='مساعدة_الأمر')
    async def command_help(self, ctx, *, name: str):
        command = self.bot.get_command(name.replace('!', '').strip())
        if not command:
            return await ctx.reply('❌ ما لقيت هذا الأمر.')
        await ctx.reply(f'📖 **!{command.name}**\nالاستخدام: `{command.signature or "بدون متغيرات"}`')


async def setup(bot):
    await bot.add_cog(Multiword(bot))
