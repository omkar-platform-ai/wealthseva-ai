import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from origin_verify import OriginVerifyMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rate_limit import limiter
from routers import chat, portfolio, risk, insights, goals, idbi, tts, nudges

app = FastAPI(
    title="WealthSeva AI",
    description="AI-powered multilingual wealth advisor for IDBI Bank",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Response headers are NOT readable cross-origin unless exposed. The
    # frontend reads X-Detected-Language to drive the language-continuity chip
    # and pick the correct TTS voice for the reply.
    expose_headers=["X-Detected-Language", "X-Grounding-Sources"],
)
# Gate the public (AuthType NONE) Lambda Function URL behind a shared secret
# header that CloudFront adds. No-op until ORIGIN_VERIFY_SECRET is set — set it
# via `aws lambda update-function-configuration` AFTER the image carrying this
# middleware is live (never in the same deploy, to avoid a lockout). Registered
# after CORSMiddleware so it is the outermost layer (Starlette wraps LIFO).
# See backend/origin_verify.py.
app.add_middleware(OriginVerifyMiddleware)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(risk.router, prefix="/api", tags=["Risk"])
app.include_router(insights.router, prefix="/api", tags=["Insights"])
app.include_router(goals.router, prefix="/api", tags=["Goals"])
app.include_router(idbi.router, prefix="/api", tags=["IDBI Sandbox"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(nudges.router, prefix="/api", tags=["Nudges"])

# Shadow mounts under /v2/api for a CloudFront /v2/* canary (no path-strip
# needed on the CFN origin). Mirrors every /api route.
app.include_router(chat.router, prefix="/v2/api", tags=["Chat"])
app.include_router(portfolio.router, prefix="/v2/api", tags=["Portfolio"])
app.include_router(risk.router, prefix="/v2/api", tags=["Risk"])
app.include_router(insights.router, prefix="/v2/api", tags=["Insights"])
app.include_router(goals.router, prefix="/v2/api", tags=["Goals"])
app.include_router(idbi.router, prefix="/v2/api", tags=["IDBI Sandbox"])
app.include_router(tts.router, prefix="/v2/api", tags=["TTS"])
app.include_router(nudges.router, prefix="/v2/api", tags=["Nudges"])


@app.get("/health")
@limiter.exempt
async def health(request: Request):
    return {"status": "ok", "service": "wealthseva-ai-backend"}
