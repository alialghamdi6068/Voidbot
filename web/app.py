from flask import Flask
from config import SESSION_SECRET


def create_app(bot):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SESSION_SECRET
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

    from web.auth import register_auth
    from web.dashboard import register_dashboard
    from web.api import register_api

    register_auth(app, bot)
    register_dashboard(app, bot)
    register_api(app, bot)

    @app.get('/health')
    def health():
        return {'status': 'ok', 'bot_ready': bot.is_ready(), 'guilds': len(bot.guilds)}

    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('404.html'), 404

    return app
