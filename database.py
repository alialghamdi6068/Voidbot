import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (guild_id INTEGER PRIMARY KEY, data TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, moderator_id INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS levels (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, xp INTEGER NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 0, last_message REAL NOT NULL DEFAULT 0, PRIMARY KEY(guild_id,user_id));
CREATE TABLE IF NOT EXISTS afk (guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(guild_id,user_id));
CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER, action TEXT NOT NULL, details TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""

def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()

@contextmanager
def connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def get_guild_data(guild_id):
    import json
    with connection() as conn:
        row = conn.execute('SELECT data FROM guild_settings WHERE guild_id=?', (guild_id,)).fetchone()
        return json.loads(row['data']) if row else {}

def set_guild_data(guild_id, data):
    import json
    payload = json.dumps(data, ensure_ascii=False)
    with connection() as conn:
        conn.execute('INSERT INTO guild_settings(guild_id,data) VALUES(?,?) ON CONFLICT(guild_id) DO UPDATE SET data=excluded.data', (guild_id, payload))

def log_activity(guild_id, action, details='', user_id=None):
    with connection() as conn:
        conn.execute('INSERT INTO activity(guild_id,user_id,action,details) VALUES(?,?,?,?)', (guild_id, user_id, action, details))

init_db()
