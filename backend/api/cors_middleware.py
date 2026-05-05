"""
Custom CORS Middleware for Development
Handles dynamic localhost origin validation
"""

import re
from typing import Sequence
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send, Message


class DevelopmentCORSMiddleware:
    """
    Custom CORS middleware for development that accepts all localhost variations.
    
    In development mode, this middleware accepts requests from any localhost origin
    (localhost or 127.0.0.1 with any port), while still maintaining security by
    rejecting non-localhost origins.
    
    In production, use FastAPI's built-in CORSMiddleware with a static whitelist.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Sequence[str] = (),
        allow_credentials: bool = False,
        allow_methods: Sequence[str] = ("GET",),
        allow_headers: Sequence[str] = (),
        expose_headers: Sequence[str] = (),
        max_age: int = 600,
    ):
        self.app = app
        self.allow_origins = list(allow_origins)
        self.allow_credentials = allow_credentials
        # Convert "*" to explicit list of methods for browser compatibility
        if allow_methods == ["*"] or "*" in allow_methods:
            self.allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
        else:
            self.allow_methods = list(allow_methods)
        # Convert "*" to explicit list of headers for browser compatibility
        if allow_headers == ["*"] or "*" in allow_headers:
            self.allow_headers = ["*"]  # Keep "*" for headers as it's widely supported
        else:
            self.allow_headers = list(allow_headers)
        self.expose_headers = list(expose_headers)
        self.max_age = max_age
        
        # Regex pattern to match localhost variations
        self.localhost_pattern = re.compile(r"^http://(localhost|127\.0\.0\.1)(:[0-9]+)?$")
    
    def is_allowed_origin(self, origin: str) -> bool:
        """Check if the origin is allowed (localhost variations or whitelist)"""
        # Check if it matches localhost pattern
        if self.localhost_pattern.match(origin):
            return True
        
        # Check if it's in the explicit whitelist
        if origin in self.allow_origins:
            return True
        
        return False
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get the origin header
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        
        # Handle preflight requests
        if scope["method"] == "OPTIONS" and origin and self.is_allowed_origin(origin):
            response_headers = [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-methods", ", ".join(self.allow_methods).encode()),
                (b"access-control-max-age", str(self.max_age).encode()),
                (b"content-length", b"0"),
            ]
            
            if self.allow_credentials:
                response_headers.append((b"access-control-allow-credentials", b"true"))
            
            # Get requested headers
            requested_headers = headers.get("access-control-request-headers")
            if requested_headers:
                response_headers.append((b"access-control-allow-headers", requested_headers.encode()))
            elif self.allow_headers:
                response_headers.append((b"access-control-allow-headers", ", ".join(self.allow_headers).encode()))
            
            if self.expose_headers:
                response_headers.append((b"access-control-expose-headers", ", ".join(self.expose_headers).encode()))
            
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": response_headers,
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })
            return
        
        # For non-preflight requests, add CORS headers to the response
        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start" and origin and self.is_allowed_origin(origin):
                headers = MutableHeaders(scope=message)
                headers["Access-Control-Allow-Origin"] = origin
                if self.allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
                if self.expose_headers:
                    headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            await send(message)
        
        await self.app(scope, receive, send_with_cors)
