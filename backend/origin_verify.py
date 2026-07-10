"""Origin-verify gate for the public (AuthType NONE) Lambda Function URL.

CloudFront adds the ``x-origin-verify`` header on every origin request; a direct
hit to the Function URL omits it. This middleware rejects requests lacking the
header so the public URL can't be driven while bypassing CloudFront.

Behaviour:
  - ``ORIGIN_VERIFY_SECRET`` unset  -> not enforced (feature flag off; lets us
    validate the Function URL now, before CloudFront is wired at cutover).
  - secret set + header missing/wrong -> 403 in the project's {"error","code"} format.
  - secret set + header matches -> request proceeds.

``/health`` is always exempt so health probes work without the header.
``hmac.compare_digest`` avoids a timing side-channel.
"""
import hmac
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_EXEMPT_PATHS = {"/health"}


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
