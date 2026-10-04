from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = monotonic()
        cutoff = now - settings.rate_limit_window_seconds

        with self.lock:
            timestamps = self.requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= settings.rate_limit_requests:
                response = JSONResponse(
                    {"detail": "Rate limit exceeded. Please try again shortly."},
                    status_code=429,
                    headers={"Retry-After": str(settings.rate_limit_window_seconds)},
                )
                await response(scope, receive, send)
                return
            timestamps.append(now)

        await self.app(scope, receive, send)
