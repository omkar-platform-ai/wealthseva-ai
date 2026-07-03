import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import chat, portfolio, risk, insights, goals, idbi

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

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
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(risk.router, prefix="/api", tags=["Risk"])
app.include_router(insights.router, prefix="/api", tags=["Insights"])
app.include_router(goals.router, prefix="/api", tags=["Goals"])
app.include_router(idbi.router, prefix="/api", tags=["IDBI Sandbox"])


@app.get("/health")
@limiter.exempt
async def health(request: Request):
    return {"status": "ok", "service": "wealthseva-ai-backend"}
