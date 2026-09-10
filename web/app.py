from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from config import SESSION_SECRET
from web.security import csrf_token


def create_app(bot):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SESSION_SECRET
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=True,
        MAX_CONTENT_LENGTH=256 * 1024,
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    @app.context_processor
    def inject_security():
        return {'csrf_token': csrf_token()}

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://cdn.discordapp.com https://media.discordapp.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        )
        if request_is_secure():
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

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
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def too_large(error):
        return render_template('error.html', title='الطلب كبير جدًا', message='البيانات المرسلة أكبر من الحد المسموح.'), 413

    @app.errorhandler(429)
    def too_many(error):
        return render_template('error.html', title='محاولات كثيرة', message='تم تجاوز عدد المحاولات المسموح بها. حاول لاحقًا.'), 429

    return app


def request_is_secure():
    from flask import request
    return request.is_secure
