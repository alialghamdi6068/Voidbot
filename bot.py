import asyncio
import threading

import discord
from discord.ext import commands
from flask import Flask

from config import BOT_PREFIX, BOT_NAME, HOST, PORT, DISCORD_TOKEN
from database import init_db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)

app = Flask(__name__)

@app.get('/')
def home():
    return f'<h1>{BOT_NAME} Dashboard</h1><p>Dashboard is online.</p>'

@app.get('/health')
def health():
    return {'status': 'ok', 'bot_ready': bot.is_ready()}


async def load_cogs():
    cog_names = [
        'moderation', 'tickets', 'applications', 'levels', 'welcome', 'logs',
        'giveaways', 'suggestions', 'afk', 'autoreply', 'autorole',
        'announcements', 'reminders', 'scheduler', 'utility', 'owner'
    ]
    for name in cog_names:
        try:
            await bot.load_extension(f'cogs.{name}')
        except commands.ExtensionNotFound:
            continue
        except Exception as exc:
            print(f'[Flame] Failed to load cogs.{name}: {exc}')


@bot.event
async def on_ready():
    print(f'[Flame] Logged in as {bot.user} | Guilds: {len(bot.guilds)}')
    try:
        synced = await bot.tree.sync()
        print(f'[Flame] Synced {len(synced)} slash commands.')
    except Exception as exc:
        print(f'[Flame] Slash sync failed: {exc}')


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
