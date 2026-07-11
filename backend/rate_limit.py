"""Shared slowapi limiter.

Lives in its own module so both ``main.py`` (registers the limiter + handler)
and ``routers/chat.py`` (per-route ``@limiter.limit``) can import it without a
circular import — ``main`` imports the routers before it would finish defining a
local limiter.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def client_ip_key(request: Request) -> str:
    # Behind the Lambda Function URL + Web Adapter, get_remote_address may see
    # the adapter/loopback rather than the real client. Prefer the leftmost
    # X-Forwarded-For entry (the original client) when present. XFF
    # trustworthiness here is deploy-verified; if keys collapse to one, switch
    # the /chat limit to a deliberate global cap.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip_key, default_limits=["30/minute"])
