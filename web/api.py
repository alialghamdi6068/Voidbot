from flask import request, jsonify
from database import get_guild_data, set_guild_data
from web.dashboard import logged_in
from web.auth import managed_guild_ids

ALLOWED_SETTINGS = {
    'welcome_channel_id', 'welcome_message', 'auto_role_id', 'log_channel_id',
    'ticket_category_id', 'ticket_panel_channel_id', 'ticket_support_role_id', 'ticket_log_channel_id',
    'applications_channel_id', 'applications_log_channel_id',
    'suggestions_channel_id', 'suggestions_log_channel_id',
    'level_channel_id', 'level_announce', 'levels_enabled', 'xp_min', 'xp_max', 'level_cooldown',
    'giveaways_channel_id', 'autoreply_channel_id', 'announcements_channel_id',
    'scheduler_channel_id', 'reminder_channel_id', 'afk_channel_id'
}

INTEGER_SETTINGS = {
    'welcome_channel_id', 'auto_role_id', 'log_channel_id',
    'ticket_category_id', 'ticket_panel_channel_id', 'ticket_support_role_id', 'ticket_log_channel_id',
    'applications_channel_id', 'applications_log_channel_id',
    'suggestions_channel_id', 'suggestions_log_channel_id', 'level_channel_id',
    'giveaways_channel_id', 'autoreply_channel_id', 'announcements_channel_id',
    'scheduler_channel_id', 'reminder_channel_id', 'afk_channel_id',
    'xp_min', 'xp_max', 'level_cooldown'
}

BOOLEAN_SETTINGS = {'level_announce', 'levels_enabled'}


def register_api(app, bot):
    @app.post('/api/guild/<int:guild_id>/settings')
    @logged_in
    def save_settings(guild_id):
        guild = bot.get_guild(guild_id)
        if guild_id not in managed_guild_ids() or not guild:
            return jsonify({'ok': False, 'error': 'غير مصرح لك بإدارة هذا السيرفر.'}), 403

        payload = request.get_json(silent=True) or {}
        data = get_guild_data(guild_id)

        action = payload.get('autoreply_action')
        if action in ('add', 'delete'):
            replies = dict(data.get('autoreplies', {}))
            trigger = str(payload.get('trigger', '')).strip()[:100]
            if not trigger:
                return jsonify({'ok': False, 'error': 'اكتب كلمة الرد.'}), 400
            if action == 'add':
                response = str(payload.get('response', '')).strip()[:2000]
                if not response:
                    return jsonify({'ok': False, 'error': 'اكتب الرد.'}), 400
                replies[trigger] = response
            else:
                replies.pop(trigger, None)
            data['autoreplies'] = replies

        for key in ALLOWED_SETTINGS:
            if key not in payload:
                continue
            value = payload[key]
            if key in INTEGER_SETTINGS:
                if value in ('', None):
                    value = None
                else:
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        return jsonify({'ok': False, 'error': f'القيمة غير صحيحة: {key}'}), 400
            elif key in BOOLEAN_SETTINGS:
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    value = bool(value)
            elif key == 'welcome_message':
                value = str(value)[:2000]
            data[key] = value

        # الحفظ المباشر يستبدل بيانات السيرفر المحدد فقط ويضمن بقاء التعديلات بعد إعادة تحميل الصفحة.
        set_guild_data(guild_id, data)
        saved = get_guild_data(guild_id)
        return jsonify({'ok': True, 'settings': saved})
