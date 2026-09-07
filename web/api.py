from flask import request, jsonify
from database import get_guild_data, update_guild_data
from web.dashboard import logged_in

ALLOWED_SETTINGS = {'welcome_channel_id','welcome_message','auto_role_id','log_channel_id','ticket_category_id','applications_channel_id','suggestions_channel_id','level_channel_id','level_announce','levels_enabled','xp_min','xp_max','level_cooldown','giveaways_channel_id','autoreplies'}


def register_api(app, bot):
    @app.post('/api/guild/<int:guild_id>/settings')
    @logged_in
    def save_settings(guild_id):
        if not bot.get_guild(guild_id):
            return jsonify({'ok': False, 'error': 'Guild not found'}), 404
        payload = request.get_json(silent=True) or {}
        clean = {k: v for k, v in payload.items() if k in ALLOWED_SETTINGS}
        update_guild_data(guild_id, **clean)
        return jsonify({'ok': True, 'settings': get_guild_data(guild_id)})
