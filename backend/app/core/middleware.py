"""Security headers and rate limiting with Redis in production."""
import hashlib
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.headers.setdefault("Cache-Control", "no-store") if request.url.path.startswith("/api/") else None
        if settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple local limiter for development; Redis-backed counters in production."""
    def __init__(self, app):
        super().__init__(app)
        self._memory = defaultdict(deque)
        self._redis = None
        if settings.REDIS_URL:
            try:
                from redis.asyncio import Redis
                self._redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True,
                                              socket_connect_timeout=2, socket_timeout=2)
            except Exception:
                self._redis = None

    def _policy(self, path: str) -> tuple[int, int, str]:
        if path.endswith("/login") or "/oauth/" in path:
            return 6, 60, "login"
        if "/phone/" in path or path.endswith("/me/phone"):
            return 5, 300, "phone_auth"
        if path.endswith("/register") or "/register/" in path:
            return 5, 3600, "registration"
        if "verification" in path or "/verify-email" in path or "/verify-phone" in path:
            return 5, 300, "verification"
        if "/copilot/" in path:
            return 20, 60, "copilot"
        # Aggregate ordinary API traffic under one IP bucket; changing URL paths
        # must not create a fresh rate-limit allowance.
        return 180, 60, "api"

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or request.method in {"OPTIONS", "HEAD"}:
            return await call_next(request)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        # Disable rate limiting in test environment to avoid test flakiness
        if settings.APP_ENV == "test":
            return await call_next(request)
        limit, window, policy_name = self._policy(request.url.path)
        raw_ip = request.client.host if request.client else "unknown"
        client_key = hashlib.sha256(raw_ip.encode()).hexdigest()[:24]
        bucket = int(time.time() // window)
        key = f"freightpilot:rl:{client_key}:{policy_name}:{bucket}"
        try:
            if self._redis is not None:
                count = await self._redis.incr(key)
                if count == 1:
                    await self._redis.expire(key, window + 2)
            elif settings.is_production:
                return JSONResponse(status_code=503, content={"error": {"code": "RATE_LIMIT_BACKEND_UNAVAILABLE", "message": "Request protection is temporarily unavailable."}})
            else:
                now = time.monotonic()
                queue = self._memory[key]
                while queue and queue[0] <= now - window:
                    queue.popleft()
                queue.append(now)
                count = len(queue)
                if len(self._memory) > 5000:
                    self._memory.clear()
        except Exception:
            if settings.is_production:
                return JSONResponse(status_code=503, content={"error": {"code": "RATE_LIMIT_BACKEND_UNAVAILABLE", "message": "Request protection is temporarily unavailable."}})
            count = 0
        if count > limit:
            return JSONResponse(status_code=429, headers={"Retry-After": str(window)},
                                content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please retry later."}})
        return await call_next(request)
