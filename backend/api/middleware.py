import logging
import time
import uuid
from typing import Callable

import redis
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings

logger = logging.getLogger(__name__)


class DegradedModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from backend.infrastructure.cache import cache_client

        cache_available = cache_client.is_available

        request.state.degraded_mode = not cache_available
        request.state.cache_available = cache_available

        response = await call_next(request)

        if not cache_available:
            response.headers["X-Degraded-Mode"] = "true"
            response.headers["X-Degraded-Reason"] = "cache-unavailable"
            logger.warning(
                f"Request processed in degraded mode: {request.method} {request.url.path}"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_id = self._get_client_identifier(request)

        if self._should_rate_limit(request):
            if not self._check_rate_limit(client_id):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.rate_limit} requests per minute.",
                    headers={"Retry-After": "60"},
                )

        response = await call_next(request)
        return response

    def _get_client_identifier(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return client_ip

    def _should_rate_limit(self, request: Request) -> bool:
        path = request.url.path

        if path.endswith("/auth/login") or path.endswith("/auth/register"):
            return True

        if path.startswith("/api/") and not path.endswith("/health"):
            return True

        return False

    def _check_rate_limit(self, client_id: str) -> bool:
        try:
            current_minute = int(time.time() / 60)

            key = f"rate_limit:{client_id}:{current_minute}"

            count = self.redis_client.incr(key)

            if count == 1:
                self.redis_client.expire(key, 60)

            return count <= self.rate_limit

        except redis.RedisError as e:
            print(f"Redis error in rate limiting: {e}")
            return True


def get_redis_client() -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = f"req_{uuid.uuid4().hex[:12]}"

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.user_id = None

        authorization = request.headers.get("Authorization")
        if authorization:
            try:
                parts = authorization.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]

                    from services.auth_service import AuthService

                    payload = AuthService.verify_token(token)
                    if payload:
                        request.state.user_id = payload.get("sub")
            except Exception:
                pass

        response = await call_next(request)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)

            response_time = time.time() - start_time
            response_time_ms = response_time * 1000

            status_code = response.status_code

            log_data = {
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "response_time_ms": round(response_time_ms, 2),
                "client_ip": client_ip,
                "user_id": user_id,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }

            if response_time > 1.0:
                logger.warning(
                    f"Performance warning: {method} {path} took {response_time_ms:.2f}ms (exceeds 1 second threshold)",
                    extra={**log_data, "performance_warning": True},
                )

            if status_code >= 500:
                logger.error(
                    f"Request failed: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data,
                )
            elif status_code >= 400:
                logger.warning(
                    f"Request error: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data,
                )
            else:
                logger.info(
                    f"Request: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data,
                )

            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"

            return response

        except Exception as e:
            response_time = time.time() - start_time
            response_time_ms = response_time * 1000

            logger.error(
                f"Request exception: {method} {path} - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "response_time_ms": round(response_time_ms, 2),
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
                exc_info=True,
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _normalize_path(self, path: str) -> str:
        import re

        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        path = re.sub(r"/\d+", "/{id}", path)

        return path
