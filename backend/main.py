from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, portfolio, risk, insights, goals, idbi

app = FastAPI(
    title="WealthSeva AI",
    description="AI-powered multilingual wealth advisor for IDBI Bank",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
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
async def health():
    return {"status": "ok", "service": "wealthseva-ai-backend"}
