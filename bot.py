import asyncio
import threading

import discord
from discord.ext import commands

from config import BOT_PREFIX, BOT_NAME, HOST, PORT, DISCORD_TOKEN
from database import init_db
from web.app import create_app


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)
app = create_app(bot)


@bot.event
async def on_ready():
    print(f'[{BOT_NAME}] Logged in as {bot.user} | Guilds: {len(bot.guilds)}')
    try:
        synced = await bot.tree.sync()
        print(f'[{BOT_NAME}] Synced {len(synced)} slash commands.')
    except Exception as exc:
        print(f'[{BOT_NAME}] Slash sync failed: {exc}')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.reply('❌ ما عندك الصلاحية المطلوبة.')
    if isinstance(error, commands.BotMissingPermissions):
        return await ctx.reply('❌ البوت ناقصه صلاحية لتنفيذ الأمر.')
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply(f'❌ ناقصك المتغير: `{error.param.name}`.')
    if isinstance(error, commands.BadArgument):
        return await ctx.reply('❌ تأكد من المنشن أو الرقم أو البيانات المدخلة.')
    print(f'[{BOT_NAME}] Command error: {type(error).__name__}: {error}')
    try:
        await ctx.reply('❌ صار خطأ أثناء تنفيذ الأمر.')
    except discord.HTTPException:
        pass


async def load_cogs():
    cog_names = [
        'moderation', 'tickets', 'applications', 'levels', 'welcome', 'logs',
        'giveaways', 'suggestions', 'afk', 'autoreply', 'autorole',
        'announcements', 'reminders', 'scheduler', 'utility', 'owner'
    ]
    for name in cog_names:
        try:
            await bot.load_extension(f'cogs.{name}')
            print(f'[{BOT_NAME}] Loaded cogs.{name}')
        except commands.ExtensionNotFound:
            print(f'[{BOT_NAME}] Missing cogs.{name}; skipped.')
        except Exception as exc:
            print(f'[{BOT_NAME}] Failed to load cogs.{name}: {exc}')


def run_web():
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


async def main():
    init_db()
    await load_cogs()
    threading.Thread(target=run_web, daemon=True, name='flame-dashboard').start()
    await bot.start(DISCORD_TOKEN)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
