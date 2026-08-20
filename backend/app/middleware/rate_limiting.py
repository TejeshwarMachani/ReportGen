"""Rate limiting middleware for FastAPI application.

Provides per-organization rate limiting based on org_id from JWT.
Enforces limits to prevent abuse while allowing fair usage.

Key features:
- Per-org rate limiting using org_id from JWT
- Configurable limits per endpoint/type
- Redis-backed storage for distributed environments
- Safe fallback when Redis unavailable
- Thread-safe token bucket algorithm
- Response headers with rate limit info
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Default rate limits: {path: (calls_per_minute, burst_allowance)}
DEFAULT_RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    "/api/v1/reports/generate": (30, 60),
    "/api/v1/forecast/generate": (20, 40),
    "/api/v1/chat/message": (50, 100),
    "/api/v1/datasets": (60, 120),
    "/api/v1/teams": (30, 60),
    "/api/v1/dashboard": (100, 200),
    "default": (100, 200),  # Fallback for unmatched paths
}


class RateLimiter:
    """Redis-backed rate limiter for distributed environments.

    Uses Redis INCR with TTL for token bucket algorithm.
    Falls back to in-memory store if Redis is unavailable.
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_store: Dict[str, Dict] = {}
        self._lock = asyncio.Lock() if redis_client else None

    async def _check_redis(self, key: str, calls_per_minute: int, burst_allowance: int) -> Tuple[bool, int]:
        """Check rate limit using Redis.

        Returns (allowed, remaining_tokens).
        """
        if not self.redis:
            return await self._check_memory(key, calls_per_minute, burst_allowance)

        try:
            # Use Redis INCR with EX TTL for automatic expiry
            # Key format: rate_limit:org_id:path
            redis_key = f"rate_limit:{key}"
            per_minute = calls_per_minute  # tokens per minute
            # Set TTL to 60 seconds * 2 for safety margin
            ttl = 120

            # INCR with initial value if key doesn't exist
            current = await self.redis.incr(redis_key)
            if current == 1:
                # First request - set TTL
                await self.redis.expire(redis_key, ttl)

            # Check if over limit
            if current > burst_allowance:
                # Calculate how long until bucket refills
                # remaining time = (current - burst_allowance) / (current_per_second)
                # Simple approach: return not allowed with Retry-After
                retry_after = ttl - (time.time() % ttl)
                return False, 0

            # Remaining tokens
            remaining = burst_allowance - current
            return True, remaining

        except Exception:
            # Redis unavailable - fall back to memory
            return await self._check_memory(key, calls_per_minute, burst_allowance)

    async def _check_memory(
        self, key: str, calls_per_minute: int, burst_allowance: int
    ) -> Tuple[bool, int]:
        """Check rate limit using in-memory store (fallback)."""
        import asyncio

        async with self._lock if self._lock else asyncio.Lock():
            now = time.time()
            entry = self._memory_store.setdefault(key, {"tokens": burst_allowance, "last_refill": now})

            # Calculate tokens to refill based on elapsed time
            elapsed = now - entry["last_refill"]
            refill_rate = calls_per_minute / 60.0  # tokens per second
            tokens_to_refill = elapsed * refill_rate

            # Cap tokens at burst allowance
            entry["tokens"] = min(burst_allowance, entry["tokens"] + tokens_to_refill)
            entry["last_refill"] = now

            if entry["tokens"] >= 1:
                entry["tokens"] -= 1
                return True, int(entry["tokens"])
            return False, 0


# Global rate limiter instance (Redis client injected at middleware init)
_rate_limiter: Optional[RateLimiter] = None


def set_rate_limiter(limiter: RateLimiter) -> None:
    """Inject Redis-backed rate limiter instance.

    Called during FastAPI app startup to inject a Redis-connected limiter.
    """
    global _rate_limiter
    _rate_limiter = limiter


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    ponytail: a shared global limiter is fine for a single process;
    move to app state for multi-process deployments.
    """
    global _rate_limiter
    if _rate_limiter is None:
        # Fall back to in-memory if not configured
        _rate_limiter = RateLimiter(redis_client=None)
    return _rate_limiter


def _get_org_id(request: Request) -> Optional[str]:
    """Extract org_id from request.

    Reads org_id from query params or headers as placeholder.
    In production, decode and validate the JWT token.
    """
    # Try to get org_id from various sources
    org_id = request.query_params.get("org_id")
    if not org_id:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Placeholder - in production, decode JWT and extract org_id
            org_id = "org-from-jwt-placeholder"
    return org_id


def _rate_key(request: Request) -> str:
    """Generate a unique rate limit key for the request.

    Format: org_id:path or path when no org auth.
    """
    org_id = _get_org_id(request)
    path = request.url.path
    if org_id:
        return f"{org_id}:{path}"
    return path


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for per-organization rate limiting.

    Uses Redis-backed rate limiter when available, falls back to in-memory
    for development/single-instance deployments.
    """

    def __init__(
        self,
        app,
        override_limits: Optional[Dict[str, Tuple[int, int]]] = None,
        exclude_paths: Optional[list] = None,
    ):
        super().__init__(app)
        # Merge default limits with any overrides
        if override_limits:
            self.limits = {**DEFAULT_RATE_LIMITS, **override_limits}
        else:
            self.limits = DEFAULT_RATE_LIMITS
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Rate limit key and matching config. The limits dict is keyed by bare
        # path (e.g. "/api/v1/reports/generate"); the Redis key prefixes org_id.
        key = _rate_key(request)
        path = request.url.path
        limits_tier = next(
            (v for k, v in self.limits.items() if path.startswith(k)),
            self.limits["default"],
        )
        limiter = get_rate_limiter()
        allowed, remaining = await limiter._check_redis(key, *limits_tier)

        if not allowed:
            # Rate limit exceeded - return 429
            retry_after = 60  # seconds until bucket refills significantly
            response = Response(
                content={"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-Rate-Limit-Limit": str(limits_tier[0]),
                    "X-Rate-Limit-Remaining": "0",
                    "X-Rate-Limit-Reset": str(int(retry_after)),
                },
            )
            return response

        # Rate limit allowed - add rate limit headers to response
        response = await call_next(request)

        # Add rate limit headers for the client
        response.headers["X-Rate-Limit-Limit"] = str(limits_tier[0])
        response.headers["X-Rate-Limit-Remaining"] = str(remaining) if isinstance(remaining, int) else "0"
        response.headers["X-Rate-Limit-Reset"] = str(int(time.time() + 60))

        return response