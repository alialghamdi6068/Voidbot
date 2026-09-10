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


def _build_ticket_buttons(payload):
    buttons = []
    for i in range(1, 6):
        label = str(payload.get(f'ticket_button_label_{i}', '')).strip()[:80]
        if not label:
            continue
        emoji = str(payload.get(f'ticket_button_emoji_{i}', '🎫')).strip()[:20] or '🎫'
        style = str(payload.get(f'ticket_button_style_{i}', 'success'))
        if style not in {'primary', 'secondary', 'success', 'danger'}:
            style = 'success'
        button = {
            'label': label,
            'emoji': emoji,
            'style': style,
        }
        category_id = payload.get(f'ticket_button_category_{i}')
        role_id = payload.get(f'ticket_button_role_{i}')
        title = str(payload.get(f'ticket_button_title_{i}', '')).strip()[:256]
        description = str(payload.get(f'ticket_button_description_{i}', '')).strip()[:4000]
        if category_id:
            try:
                button['category_id'] = int(category_id)
            except (TypeError, ValueError):
                pass
        if role_id:
            try:
                button['support_role_id'] = int(role_id)
            except (TypeError, ValueError):
                pass
        if title:
            button['title'] = title
        if description:
            button['description'] = description
        buttons.append(button)
    return buttons


def _build_level_rewards(payload):
    rewards = {}
    for level in range(1, 21):
        value = payload.get(f'level_reward_{level}')
        if not value:
            continue
        try:
            rewards[str(level)] = int(value)
        except (TypeError, ValueError):
            continue
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

        if any(key.startswith('ticket_button_') for key in payload):
            data['ticket_buttons'] = _build_ticket_buttons(payload)

        if any(key.startswith('level_reward_') for key in payload):
            data['level_rewards'] = _build_level_rewards(payload)

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
                if key == 'welcome_message':
                    value = value[:2000]
                elif key == 'ticket_panel_title':
                    value = value[:256]
                elif key == 'ticket_panel_description':
                    value = value[:4000]
                else:
                    value = value[:200]
            data[key] = value

        update_guild_data(guild_id, **data)
        return jsonify({'ok': True, 'settings': get_guild_data(guild_id)})
