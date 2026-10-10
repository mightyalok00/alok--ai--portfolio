import secrets
import time
from collections import deque
from threading import Lock

from fastapi import Request

_rate_lock = Lock()
_requests: dict[str, deque[float]] = {}
_last_prune = 0.0
_MAX_RATE_LIMIT_KEYS = 10_000


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def valid_csrf(request: Request, submitted_token: str | None) -> bool:
    stored_token = request.session.get("csrf_token", "")
    return bool(submitted_token and stored_token and secrets.compare_digest(stored_token, submitted_token))


def allow_request(request: Request, limit: int = 8, window_seconds: int = 60) -> bool:
    # Lightweight single-process protection. Use a shared store at scale / across workers.
    global _last_prune
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_lock:
        # Periodically remove stale client keys so unique-IP traffic cannot grow this
        # dictionary forever. This is intentionally a bounded, single-process limiter.
        if now - _last_prune >= 300:
            stale_before = now - max(window_seconds, 300)
            stale_keys = [key for key, events in _requests.items() if not events or events[-1] < stale_before]
            for key in stale_keys:
                _requests.pop(key, None)
            _last_prune = now

        bucket = _requests.get(client)
        if bucket is None:
            if len(_requests) >= _MAX_RATE_LIMIT_KEYS:
                stale_before = now - window_seconds
                stale_keys = [key for key, events in _requests.items() if not events or events[-1] < stale_before]
                for key in stale_keys:
                    _requests.pop(key, None)
                if len(_requests) >= _MAX_RATE_LIMIT_KEYS:
                    return False
            bucket = deque()
            _requests[client] = bucket
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
    return True
