import secrets
import time
import requests
from flask import redirect, request, session, url_for, render_template
from config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI

DISCORD_API = 'https://discord.com/api/v10'


def _managed_guilds_from_token(token):
    if not token:
        return set()
    try:
        response = requests.get(
            f'{DISCORD_API}/users/@me/guilds',
            headers={'Authorization': f'Bearer {token}'},
            timeout=15,
        )
        if response.status_code != 200:
            return set()

        allowed = set()
        for guild in response.json():
            try:
                permissions = int(guild.get('permissions_new', guild.get('permissions', 0)))
            except (TypeError, ValueError):
                permissions = 0

            # MANAGE_GUILD = 0x20, ADMINISTRATOR = 0x8.
            if guild.get('owner') is True or permissions & 0x20 or permissions & 0x8:
                try:
                    allowed.add(int(guild['id']))
                except (KeyError, TypeError, ValueError):
                    continue
        return allowed
    except (requests.RequestException, ValueError, TypeError):
        return set()


def register_auth(app, bot):
    @app.get('/login')
    def login():
        # OAuth2 is configured once by the site owner in the hosting environment.
        # Never expose hosting setup instructions to normal website visitors.
        if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET or not DISCORD_REDIRECT_URI:
            return render_template(
                'error.html',
                title='تعذر تسجيل الدخول',
                message='تسجيل الدخول غير متاح حاليًا. يرجى المحاولة لاحقًا.'
            ), 503

        state = secrets.token_urlsafe(32)
        session.clear()
        session['oauth_state'] = state
        params = {
            'client_id': DISCORD_CLIENT_ID,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify guilds',
            'state': state,
        }
        query = '&'.join(f'{k}={requests.utils.quote(str(v), safe="")}' for k, v in params.items())
        return redirect(f'{DISCORD_API}/oauth2/authorize?{query}')

    @app.get('/callback')
    def callback():
        state = request.args.get('state')
        expected = session.get('oauth_state')
        if not state or not expected or state != expected:
            return render_template('error.html', title='خطأ في تسجيل الدخول', message='تعذر إكمال جلسة تسجيل الدخول. حاول مرة أخرى.'), 400

        code = request.args.get('code')
        if not code:
            session.clear()
            return render_template('error.html', title='تم إلغاء الدخول', message='لم يتم إكمال تسجيل الدخول إلى Discord.'), 400

        try:
            response = requests.post(
                f'{DISCORD_API}/oauth2/token',
                data={
                    'client_id': DISCORD_CLIENT_ID,
                    'client_secret': DISCORD_CLIENT_SECRET,
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': DISCORD_REDIRECT_URI,
                },
                timeout=15,
            )
            if response.status_code != 200:
                session.clear()
                return render_template('error.html', title='فشل تسجيل الدخول', message='تعذر تسجيل الدخول عبر Discord. تأكد من إعدادات التطبيق وحاول مرة أخرى.'), 502

            token = response.json()
            access_token = token.get('access_token')
            if not access_token:
                session.clear()
                return render_template('error.html', title='فشل تسجيل الدخول', message='تعذر إكمال تسجيل الدخول عبر Discord.'), 502

            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(f'{DISCORD_API}/users/@me', headers=headers, timeout=15)
            if user_response.status_code != 200:
                session.clear()
                return render_template('error.html', title='فشل تسجيل الدخول', message='تعذر جلب بيانات حساب Discord.'), 502

            guilds = _managed_guilds_from_token(access_token)
            user = user_response.json()

            session.clear()
            session['oauth'] = {
                'access_token': access_token,
                'refresh_token': token.get('refresh_token'),
                'expires_at': time.time() + int(token.get('expires_in', 604800)),
            }
            session['user'] = {
                'id': str(user.get('id', '')),
                'username': user.get('username'),
                'global_name': user.get('global_name'),
                'avatar': user.get('avatar'),
            }
            # Keep the exact managed-server set from the successful OAuth login.
            # This avoids a second Discord API call failing during a save request.
            session['managed_guild_ids'] = sorted(guilds)
            return redirect(url_for('servers'))
        except (requests.RequestException, ValueError, TypeError):
            session.clear()
            return render_template('error.html', title='فشل الاتصال', message='تعذر الاتصال بخوادم Discord. حاول مرة أخرى.'), 502

    @app.get('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))


def discord_token():
    return (session.get('oauth') or {}).get('access_token')


def managed_guild_ids():
    # Prefer the signed session cache created immediately after OAuth login.
    cached = session.get('managed_guild_ids')
    if isinstance(cached, list):
        result = set()
        for guild_id in cached:
            try:
                result.add(int(guild_id))
            except (TypeError, ValueError):
                continue
        return result

    return _managed_guilds_from_token(discord_token())
