from functools import wraps
from flask import render_template, redirect, session, url_for, abort, request
from database import get_guild_data, connection
from web.auth import discord_token, managed_guild_ids

SYSTEMS = {
    'welcome': ('الترحيب', '👋'),
    'tickets': ('التذاكر', '🎫'),
    'applications': ('التقديمات', '📝'),
    'levels': ('المستويات', '📈'),
    'autoreply': ('الردود التلقائية', '💬'),
    'giveaways': ('القيفاواي', '🎉'),
    'suggestions': ('الاقتراحات', '💡'),
    'logs': ('اللوق', '📋'),
    'autorole': ('الرتبة التلقائية', '🏷️'),
    'announcements': ('الإعلانات', '📢'),
    'reminders': ('التذكيرات', '⏰'),
    'scheduler': ('الجدولة', '🗓️'),
    'afk': ('الغياب', '💤'),
}


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user') or not discord_token():
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def can_manage_guild(guild):
    user = session.get('user') or {}
    user_id = user.get('id')
    if not user_id or not guild:
        return False
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False

    # صاحب السيرفر مسموح له دائماً، حتى لو قائمة OAuth guilds لم ترجع الصلاحيات بشكل صحيح.
    if guild.owner_id == user_id:
        return True

    member = guild.get_member(user_id)
    if member:
        return member.guild_permissions.manage_guild or member.guild_permissions.administrator

    # fallback لقائمة Discord OAuth2.
    return guild.id in managed_guild_ids()


def manageable_guilds(bot):
    result = []
    for guild in bot.guilds:
        if can_manage_guild(guild):
            result.append(guild)
    return result


def require_guild(guild_id, bot):
    guild = bot.get_guild(guild_id)
    if not guild:
        abort(404)
    if not can_manage_guild(guild):
        abort(403)
    return guild


def register_dashboard(app, bot):
    @app.get('/')
    def home():
        if request.args.get('code') and request.args.get('state'):
            return redirect(url_for('callback', code=request.args['code'], state=request.args['state']))
        if session.get('user'):
            return redirect(url_for('servers'))
        return render_template('index.html')

    @app.get('/servers')
    @logged_in
    def servers():
        return render_template('servers.html', user=session['user'], guilds=manageable_guilds(bot))

    @app.get('/dashboard/<int:guild_id>')
    @logged_in
    def dashboard(guild_id):
        guild = require_guild(guild_id, bot)
        with connection() as conn:
            activity_count = conn.execute('SELECT COUNT(*) c FROM activity WHERE guild_id=?', (guild_id,)).fetchone()['c']
            member_levels = conn.execute('SELECT COUNT(*) c FROM levels WHERE guild_id=?', (guild_id,)).fetchone()['c']
        return render_template('dashboard.html', user=session['user'], guild=guild, settings=get_guild_data(guild_id), systems=SYSTEMS, activity_count=activity_count, member_levels=member_levels)

    @app.get('/dashboard/<int:guild_id>/settings')
    @logged_in
    def settings(guild_id):
        return redirect(url_for('system_page', guild_id=guild_id, system='welcome'))

    @app.get('/dashboard/<int:guild_id>/system/<system>')
    @logged_in
    def system_page(guild_id, system):
        guild = require_guild(guild_id, bot)
        if system not in SYSTEMS:
            abort(404)
        import discord
        channels = [c for c in guild.channels if isinstance(c, discord.TextChannel)]
        categories = list(guild.categories)
        return render_template('system.html', user=session['user'], guild=guild, settings=get_guild_data(guild_id), channels=channels, categories=categories, roles=guild.roles, systems=SYSTEMS, current_system=system, system_title=SYSTEMS[system][0], system_icon=SYSTEMS[system][1])

    @app.get('/dashboard/<int:guild_id>/activity')
    @logged_in
    def activity(guild_id):
        guild = require_guild(guild_id, bot)
        with connection() as conn:
            rows = conn.execute('SELECT * FROM activity WHERE guild_id=? ORDER BY id DESC LIMIT 100', (guild_id,)).fetchall()
        return render_template('activity.html', user=session['user'], guild=guild, rows=rows)

    @app.get('/dashboard/<int:guild_id>/commands')
    @logged_in
    def commands_page(guild_id):
        guild = require_guild(guild_id, bot)
        return render_template('commands.html', user=session['user'], guild=guild)
