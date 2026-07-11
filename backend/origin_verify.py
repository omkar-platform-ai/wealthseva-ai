"""Origin-verify gate for the public (AuthType NONE) Lambda Function URL.

The Amplify SSR proxy (``frontend/app/api/[...path]/route.ts``) adds the
``x-origin-verify`` header when it forwards the non-chat endpoints to the
Function URL; a direct hit to the URL omits it. This middleware rejects requests
lacking the header so the public URL can't be driven while bypassing the proxy.
(CloudFront is not in front of the Function URL — CF->FURL is unsupported in
this account/region — so the proxy is the sole header injector.)

Behaviour:
  - ``ORIGIN_VERIFY_SECRET`` unset  -> not enforced (feature flag off; e.g. for
    isolated Function-URL validation or local dev).
  - secret set + header missing/wrong -> 403 in the project's {"error","code"} format.
  - secret set + header matches -> request proceeds.

``/health`` is always exempt so health probes work without the header.
``/api/chat`` is exempt because the public streaming chat surface is hit
directly by the browser (the Function URL directly, not through the SSR proxy)
so it never carries the header; it is guarded instead by rate limit + input caps
+ CORS + a kill-switch. Exact-match (not prefix), so the other endpoints stay
gated. ``hmac.compare_digest`` avoids a timing side-channel.
"""
import hmac
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_EXEMPT_PATHS = {"/health", "/api/chat"}


class OriginVerifyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        secret = os.environ.get("ORIGIN_VERIFY_SECRET")
        if not secret or request.url.path in _EXEMPT_PATHS:
            return await call_next(request)
        provided = request.headers.get("x-origin-verify", "")
        if not hmac.compare_digest(provided, secret):
            return JSONResponse(
                status_code=403,
                content={"error": "origin not allowed", "code": "ORIGIN_FORBIDDEN"},
            )
        return await call_next(request)
