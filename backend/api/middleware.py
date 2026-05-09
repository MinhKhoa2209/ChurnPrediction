"""
API Middleware

This module provides middleware for rate limiting, authentication, logging, and request tracking.
"""

import logging
import time
import uuid
from typing import Callable

import redis
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings

# Configure structured logging
logger = logging.getLogger(__name__)


class DegradedModeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and signal degraded mode operation
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check service availability and add degraded mode headers
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response with degraded mode headers if applicable
        """
        # Import here to avoid circular dependency
        from backend.infrastructure.cache import cache_client
        
        # Check cache availability
        cache_available = cache_client.is_available
        
        # Store degraded mode status in request state
        request.state.degraded_mode = not cache_available
        request.state.cache_available = cache_available
        
        # Process request
        response = await call_next(request)
        
        # Add degraded mode header if cache is unavailable (Requirement 30.2, 30.5)
        if not cache_available:
            response.headers["X-Degraded-Mode"] = "true"
            response.headers["X-Degraded-Reason"] = "cache-unavailable"
            logger.warning(
                f"Request processed in degraded mode: {request.method} {request.url.path}"
            )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    Requirement 23.5: Implement rate limiting of 100 requests per minute per User
    Requirement 1.3: Rate limiting for login attempts (100 requests/minute)
    """

    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = settings.rate_limit_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and apply rate limiting
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Get client identifier (IP address or user ID if authenticated)
        client_id = self._get_client_identifier(request)
        
        # Check if this endpoint should be rate limited
        if self._should_rate_limit(request):
            # Check rate limit
            if not self._check_rate_limit(client_id):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.rate_limit} requests per minute.",
                    headers={"Retry-After": "60"}
                )
        
        # Process request
        response = await call_next(request)
        return response

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client
        Uses IP address as the primary identifier
        
        Args:
            request: HTTP request
            
        Returns:
            Client identifier string
        """
        # Try to get real IP from X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Fall back to direct client IP
            client_ip = request.client.host if request.client else "unknown"
        
        return client_ip

    def _should_rate_limit(self, request: Request) -> bool:
        """
        Determine if the request should be rate limited
        
        Args:
            request: HTTP request
            
        Returns:
            True if rate limiting should be applied
        """
        # Rate limit authentication endpoints
        path = request.url.path
        
        # Apply rate limiting to login endpoint
        if path.endswith("/auth/login") or path.endswith("/auth/register"):
            return True
        
        # Apply rate limiting to all API endpoints (except health checks)
        if path.startswith("/api/") and not path.endswith("/health"):
            return True
        
        return False

    def _check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit
        Uses sliding window algorithm with Redis
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        try:
            # Get current minute timestamp
            current_minute = int(time.time() / 60)
            
            # Create Redis key for this client and minute
            key = f"rate_limit:{client_id}:{current_minute}"
            
            # Increment counter
            count = self.redis_client.incr(key)
            
            # Set expiration on first request (TTL: 60 seconds)
            if count == 1:
                self.redis_client.expire(key, 60)
            
            # Check if limit exceeded
            return count <= self.rate_limit
            
        except redis.RedisError as e:
            # If Redis is unavailable, allow the request (fail open)
            # Log the error in production
            print(f"Redis error in rate limiting: {e}")
            return True


def get_redis_client() -> redis.Redis:
    """
    Create Redis client for rate limiting
    
    Returns:
        Redis client instance
    """
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


class RequestIDMiddleware:
    """
    Pure ASGI middleware to generate and attach request IDs to all requests
    Requirement 20.1, 20.3: Include request ID in error responses for tracking
    
    Note: Using pure ASGI middleware instead of BaseHTTPMiddleware to avoid
    issues with exception handling in Python 3.11+ with ExceptionGroups
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """
        ASGI middleware implementation
        
        Args:
            scope: ASGI scope dict
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Store in scope state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id
        
        async def send_with_request_id(message):
            """Add request ID header to response"""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_request_id)


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and attach user context to request state
    Requirement 20.1: Log errors with user ID for audit trails
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract user ID from JWT token and attach to request state
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        # Initialize user_id as None
        request.state.user_id = None
        
        # Try to extract user ID from Authorization header
        authorization = request.headers.get("Authorization")
        if authorization:
            try:
                # Extract token from "Bearer <token>" format
                parts = authorization.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    
                    # Import here to avoid circular dependency
                    from services.auth_service import AuthService
                    
                    # Verify token and extract user ID
                    payload = AuthService.verify_token(token)
                    if payload:
                        request.state.user_id = payload.get("sub")
            except Exception:
                # If token verification fails, leave user_id as None
                # The actual authentication will be handled by dependencies
                pass
        
        # Process request
        response = await call_next(request)
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests with method, path, status code, and response time
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log API request details
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response with timing information
        """
        # Start timing
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, "user_id", None)
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            response_time_ms = response_time * 1000
            
            # Get status code
            status_code = response.status_code
            
            # Log request with all details (Requirement 20.5)
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
            
            # Emit performance warning if response time exceeds 1 second (Requirement 21.7)
            if response_time > 1.0:
                logger.warning(
                    f"Performance warning: {method} {path} took {response_time_ms:.2f}ms (exceeds 1 second threshold)",
                    extra={**log_data, "performance_warning": True}
                )
            
            # Use appropriate log level based on status code
            if status_code >= 500:
                logger.error(
                    f"Request failed: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data
                )
            elif status_code >= 400:
                logger.warning(
                    f"Request error: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data
                )
            else:
                logger.info(
                    f"Request: {method} {path} - {status_code} - {response_time_ms:.2f}ms",
                    extra=log_data
                )
            
            # Add response time header for debugging
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calculate response time even for exceptions
            response_time = time.time() - start_time
            response_time_ms = response_time * 1000
            
            # Log exception
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
                exc_info=True
            )
            
            # Re-raise exception to be handled by exception handlers
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address
        """
        # Try to get real IP from X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize API path to reduce cardinality in metrics
        Replaces UUIDs and numeric IDs with placeholders
        
        Args:
            path: Original request path
            
        Returns:
            Normalized path with placeholders
        """
        import re
        
        # Replace UUIDs with {id}
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs with {id}
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path

