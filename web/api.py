from flask import request, jsonify
from database import get_guild_data, update_guild_data
from web.dashboard import logged_in
from web.auth import managed_guild_ids

ALLOWED_SETTINGS={'welcome_channel_id','welcome_message','auto_role_id','log_channel_id','ticket_category_id','applications_channel_id','suggestions_channel_id','level_channel_id','level_announce','levels_enabled','xp_min','xp_max','level_cooldown','giveaways_channel_id'}

def register_api(app, bot):
    @app.post('/api/guild/<int:guild_id>/settings')
    @logged_in
    def save_settings(guild_id):
        if guild_id not in managed_guild_ids() or not bot.get_guild(guild_id):
            return jsonify({'ok':False,'error':'غير مصرح لك بإدارة هذا السيرفر.'}),403
        payload=request.get_json(silent=True) or {}
        data=get_guild_data(guild_id)
        action=payload.get('autoreply_action')
        if action in ('add','delete'):
            replies=dict(data.get('autoreplies',{}))
            trigger=str(payload.get('trigger','')).strip()[:100]
            if not trigger:return jsonify({'ok':False,'error':'اكتب كلمة الرد.'}),400
            if action=='add':
                response=str(payload.get('response','')).strip()[:2000]
                if not response:return jsonify({'ok':False,'error':'اكتب الرد.'}),400
                replies[trigger]=response
            else: replies.pop(trigger,None)
            update_guild_data(guild_id,autoreplies=replies)
        clean={k:v for k,v in payload.items() if k in ALLOWED_SETTINGS}
        if clean:update_guild_data(guild_id,**clean)
        return jsonify({'ok':True,'settings':get_guild_data(guild_id)})
