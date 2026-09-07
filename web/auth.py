import secrets
import time
import requests
from flask import redirect, request, session, url_for, render_template
from config import DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI

DISCORD_API = 'https://discord.com/api/v10'


def register_auth(app, bot):
    @app.get('/login')
    def login():
        if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET or not DISCORD_REDIRECT_URI:
            return render_template('error.html', title='OAuth2 غير مكتمل', message='أضف إعدادات Discord OAuth2 في الاستضافة.'), 500
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        params = {'client_id': DISCORD_CLIENT_ID, 'redirect_uri': DISCORD_REDIRECT_URI, 'response_type': 'code', 'scope': 'identify guilds', 'state': state}
        query = '&'.join(f'{k}={requests.utils.quote(str(v), safe="")}' for k, v in params.items())
        return redirect(f'{DISCORD_API}/oauth2/authorize?{query}')

    @app.get('/callback')
    def callback():
        if request.args.get('state') != session.pop('oauth_state', None):
            return render_template('error.html', title='خطأ في تسجيل الدخول', message='جلسة تسجيل الدخول غير صالحة.'), 400
        code = request.args.get('code')
        if not code:
            return render_template('error.html', title='تم إلغاء الدخول', message='لم يتم إكمال تسجيل الدخول إلى Discord.'), 400
        response = requests.post(f'{DISCORD_API}/oauth2/token', data={'client_id': DISCORD_CLIENT_ID, 'client_secret': DISCORD_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': DISCORD_REDIRECT_URI}, timeout=15)
        if response.status_code != 200:
            return render_template('error.html', title='فشل OAuth2', message='Discord رفض تسجيل الدخول.'), 502
        token = response.json()
        session['oauth'] = {'access_token': token['access_token'], 'refresh_token': token.get('refresh_token'), 'expires_at': time.time() + int(token.get('expires_in', 604800))}
        user_response = requests.get(f'{DISCORD_API}/users/@me', headers={'Authorization': f'Bearer {token["access_token"]}'}, timeout=15)
        if user_response.status_code != 200:
            session.clear()
            return redirect(url_for('login'))
        session['user'] = user_response.json()
        return redirect(url_for('servers'))

    @app.get('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))


def discord_token():
    data = session.get('oauth') or {}
    return data.get('access_token')
