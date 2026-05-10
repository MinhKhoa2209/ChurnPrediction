import re
from typing import Sequence

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class DevelopmentCORSMiddleware:
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

        if allow_methods == ["*"] or "*" in allow_methods:
            self.allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
        else:
            self.allow_methods = list(allow_methods)

        if allow_headers == ["*"] or "*" in allow_headers:
            self.allow_headers = ["*"]
        else:
            self.allow_headers = list(allow_headers)
        self.expose_headers = list(expose_headers)
        self.max_age = max_age

        self.localhost_pattern = re.compile(r"^http://(localhost|127\.0\.0\.1)(:[0-9]+)?$")

    def is_allowed_origin(self, origin: str) -> bool:
        if self.localhost_pattern.match(origin):
            return True

        if origin in self.allow_origins:
            return True

        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")

        if scope["method"] == "OPTIONS" and origin and self.is_allowed_origin(origin):
            response_headers = [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-methods", ", ".join(self.allow_methods).encode()),
                (b"access-control-max-age", str(self.max_age).encode()),
                (b"content-length", b"0"),
            ]

            if self.allow_credentials:
                response_headers.append((b"access-control-allow-credentials", b"true"))

            requested_headers = headers.get("access-control-request-headers")
            if requested_headers:
                response_headers.append(
                    (b"access-control-allow-headers", requested_headers.encode())
                )
            elif self.allow_headers:
                response_headers.append(
                    (b"access-control-allow-headers", ", ".join(self.allow_headers).encode())
                )

            if self.expose_headers:
                response_headers.append(
                    (b"access-control-expose-headers", ", ".join(self.expose_headers).encode())
                )

            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": response_headers,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"",
                }
            )
            return

        async def send_with_cors(message: Message) -> None:
            if (
                message["type"] == "http.response.start"
                and origin
                and self.is_allowed_origin(origin)
            ):
                headers = MutableHeaders(scope=message)
                headers["Access-Control-Allow-Origin"] = origin
                if self.allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
                if self.expose_headers:
                    headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
            await send(message)

        await self.app(scope, receive, send_with_cors)
