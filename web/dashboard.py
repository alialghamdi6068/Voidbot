from functools import wraps
from flask import render_template, redirect, session, url_for, abort
from database import get_guild_data, connection
from web.auth import discord_token


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user') or not discord_token():
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def manageable_guilds(bot):
    guilds = []
    for guild in bot.guilds:
        guilds.append(guild)
    return guilds


def register_dashboard(app, bot):
    @app.get('/')
    def home():
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
        guild = bot.get_guild(guild_id)
        if not guild:
            abort(404)
        with connection() as conn:
            activity_count = conn.execute('SELECT COUNT(*) c FROM activity WHERE guild_id=?', (guild_id,)).fetchone()['c']
            member_levels = conn.execute('SELECT COUNT(*) c FROM levels WHERE guild_id=?', (guild_id,)).fetchone()['c']
        return render_template('dashboard.html', user=session['user'], guild=guild, settings=get_guild_data(guild_id), activity_count=activity_count, member_levels=member_levels)

    @app.get('/dashboard/<int:guild_id>/settings')
    @logged_in
    def settings(guild_id):
        guild = bot.get_guild(guild_id)
        if not guild:
            abort(404)
        channels = [c for c in guild.channels if isinstance(c, __import__('discord').TextChannel)]
        categories = [c for c in guild.categories]
        return render_template('settings.html', user=session['user'], guild=guild, settings=get_guild_data(guild_id), channels=channels, categories=categories)

    @app.get('/dashboard/<int:guild_id>/activity')
    @logged_in
    def activity(guild_id):
        guild = bot.get_guild(guild_id)
        if not guild:
            abort(404)
        with connection() as conn:
            rows = conn.execute('SELECT * FROM activity WHERE guild_id=? ORDER BY id DESC LIMIT 100', (guild_id,)).fetchall()
        return render_template('activity.html', user=session['user'], guild=guild, rows=rows)

    @app.get('/dashboard/<int:guild_id>/commands')
    @logged_in
    def commands_page(guild_id):
        guild = bot.get_guild(guild_id)
        if not guild:
            abort(404)
        return render_template('commands.html', user=session['user'], guild=guild)
