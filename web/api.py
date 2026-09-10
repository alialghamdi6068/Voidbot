from flask import request, jsonify
from database import get_guild_data, update_guild_data
from web.dashboard import logged_in, can_manage_guild

ALLOWED_SETTINGS = {
    'welcome_channel_id', 'welcome_message', 'auto_role_id', 'log_channel_id',
    'ticket_category_id', 'ticket_panel_channel_id', 'ticket_log_channel_id', 'ticket_support_role_id',
    'ticket_panel_title', 'ticket_panel_description', 'ticket_panel_footer',
    'applications_channel_id', 'applications_log_channel_id',
    'suggestions_channel_id', 'suggestions_log_channel_id',
    'level_channel_id', 'level_announce', 'levels_enabled', 'xp_min', 'xp_max', 'level_cooldown',
    'giveaways_channel_id', 'autoreply_channel_id', 'announcements_channel_id',
    'scheduler_channel_id', 'reminder_channel_id', 'afk_channel_id'
}

INTEGER_SETTINGS = {
    'welcome_channel_id', 'auto_role_id', 'log_channel_id', 'ticket_category_id',
    'ticket_panel_channel_id', 'ticket_log_channel_id', 'ticket_support_role_id',
    'applications_channel_id', 'applications_log_channel_id',
    'suggestions_channel_id', 'suggestions_log_channel_id',
    'level_channel_id', 'giveaways_channel_id', 'autoreply_channel_id',
    'announcements_channel_id', 'scheduler_channel_id', 'reminder_channel_id', 'afk_channel_id',
    'xp_min', 'xp_max', 'level_cooldown'
}

BOOLEAN_SETTINGS = {'level_announce', 'levels_enabled'}


def _get_bot_guild(bot, guild_id):
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        return None
    try:
        guilds = list(bot.guilds)
    except Exception:
        return None
    for guild in guilds:
        if guild.id == guild_id:
            return guild
    return None


def _clean_ticket_buttons(value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:5]:
        if not isinstance(item, dict):
            continue
        label = str(item.get('label', '')).strip()[:80]
        if not label:
            continue
        button = {
            'label': label,
            'emoji': str(item.get('emoji') or '🎫').strip()[:20] or '🎫',
            'style': item.get('style') if item.get('style') in {'primary', 'secondary', 'success', 'danger'} else 'success'
        }
        for key in ('category_id', 'support_role_id'):
            if item.get(key):
                try:
                    button[key] = int(item[key])
                except (TypeError, ValueError):
                    pass
        if item.get('title'):
            button['title'] = str(item['title'])[:256]
        if item.get('description'):
            button['description'] = str(item['description'])[:4000]
        result.append(button)
    return result


def _clean_level_rewards(value):
    if not isinstance(value, dict):
        return {}
    rewards = {}
    for level, role_id in value.items():
        try:
            level_int = int(level)
            role_int = int(role_id)
        except (TypeError, ValueError):
            continue
        if 1 <= level_int <= 100 and role_int > 0:
            rewards[str(level_int)] = role_int
    return rewards


def register_api(app, bot):
    @app.post('/api/guild/<int:guild_id>/settings')
    @logged_in
    def save_settings(guild_id):
        guild = _get_bot_guild(bot, guild_id)
        if guild is None:
            return jsonify({'ok': False, 'error': 'السيرفر غير موجود أو البوت غير متصل به.'}), 404

        if not can_manage_guild(guild):
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

        if 'ticket_buttons' in payload:
            data['ticket_buttons'] = _clean_ticket_buttons(payload.get('ticket_buttons'))

        if 'level_rewards' in payload:
            data['level_rewards'] = _clean_level_rewards(payload.get('level_rewards'))

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
                value = bool(value)
            elif key in {'welcome_message', 'ticket_panel_title', 'ticket_panel_description', 'ticket_panel_footer'}:
                value = str(value)
                limits = {
                    'welcome_message': 2000,
                    'ticket_panel_title': 256,
                    'ticket_panel_description': 4000,
                    'ticket_panel_footer': 200,
                }
                value = value[:limits[key]]
            data[key] = value

        update_guild_data(guild_id, **data)
        return jsonify({'ok': True, 'settings': get_guild_data(guild_id)})
