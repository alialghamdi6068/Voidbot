import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import abort, request, session


_RATE_BUCKETS = defaultdict(deque)
_RATE_LIMITS = {
    'login': (10, 60),
    'callback': (10, 60),
    'api': (30, 60),
}


def client_ip():
    # Do not trust arbitrary forwarded headers. ProxyFix in app.py makes
    # request.remote_addr the trusted proxy-derived client address.
    return request.remote_addr or 'unknown'


def rate_limit(bucket):
    limit, window = _RATE_LIMITS[bucket]
    key = (bucket, client_ip())
    now = time.monotonic()
    events = _RATE_BUCKETS[key]
    while events and now - events[0] >= window:
        events.popleft()
    if len(events) >= limit:
        abort(429, description='تم تجاوز عدد المحاولات المسموح بها. حاول لاحقًا.')
    events.append(now)


def csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token


def validate_csrf():
    expected = session.get('csrf_token')
    supplied = request.headers.get('X-CSRF-Token', '')
    if not expected or not supplied or not secrets.compare_digest(str(supplied), str(expected)):
        abort(403, description='طلب غير صالح.')


def protected_post(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        rate_limit('api')
        validate_csrf()
        return fn(*args, **kwargs)
    return wrapper
