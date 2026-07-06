from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, FileResponse
from models.schemas import Language
from services.claude_service import analyze_portfolio
import pandas as pd
import io
import os

router = APIRouter()

# Security limits
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
REQUIRED_COLUMNS = {"Ticker", "Category", "Value", "Units"}

# Bundled synthetic sample CAS (WEA-73). The PDF at data/sample_cas.pdf is the
# "look, a real consolidated statement" visual; SAMPLE_CAS_HOLDINGS below is the
# DEMO SOURCE OF TRUTH — the exact known-good normalised records for that sample
# in the same {Ticker, Category, Value, Units} shape the CSV path feeds to
# analyze_portfolio. Numbers here MUST stay in sync with the PDF. Zero parse risk:
# the /cas-sample endpoint never depends on live PDF parsing.
SAMPLE_CAS_PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_cas.pdf"
)
SAMPLE_CAS_HOLDINGS: list[dict] = [
    # Demat equity holdings
    {"Ticker": "Reliance Industries Ltd", "Category": "Equity", "Value": 145000, "Units": 50},
    {"Ticker": "HDFC Bank Ltd", "Category": "Equity", "Value": 96000, "Units": 60},
    {"Ticker": "Infosys Ltd", "Category": "Equity", "Value": 78000, "Units": 50},
    # Mutual fund folios
    {"Ticker": "SBI Bluechip Fund", "Category": "Equity", "Value": 62000, "Units": 700},
    {"Ticker": "HDFC Corporate Bond Fund", "Category": "Debt", "Value": 110000, "Units": 3600},
    {"Ticker": "ICICI Pru Short Term Fund", "Category": "Debt", "Value": 70000, "Units": 1400},
    {"Ticker": "SBI Liquid Fund", "Category": "Liquid", "Value": 90000, "Units": 24},
    {"Ticker": "Nippon India Gold Savings Fund", "Category": "Gold", "Value": 45000, "Units": 1800},
]

# Sample portfolios for the "Try with Sample" picker. Each is a tiny CSV with
# columns Ticker,Category,Value,Units. Value/Units are PLAIN numbers (no ₹, no
# thousands commas) so PapaParse dynamicTyping reads them as numerics, and no
# commas appear inside fund names (a comma would shift columns and break parsing).
SAMPLE_PORTFOLIOS: dict[str, str] = {
    # Ramesh persona — pinned to MOCK_PORTFOLIO (total ₹5,09,620, idle-cash story).
    "balanced": """Ticker,Category,Value,Units
HDFC Flexi Cap Fund,Flexi Cap Equity,114240,60
SBI Blue Chip Fund,Large Cap Equity,61880,703.18
HDFC Short Term Debt Fund,Short Duration Debt,84200,2854.24
SBI Gold ETF,Gold ETF,9300,150
ICICI Pru Liquid Fund,Liquid,240000,640""",
    # Capital preservation ~₹5.0L — corporate bond / gilt / liquid heavy + small large cap.
    "conservative": """Ticker,Category,Value,Units
HDFC Corporate Bond Fund,Corporate Bond,200000,6666.67
SBI Magnum Gilt Fund,Gilt,130000,2000
ICICI Pru Liquid Fund,Liquid,120000,320
SBI Blue Chip Fund,Large Cap Equity,50000,568.18""",
    # Growth ~₹6.0L — flexi / small / mid / international equity + small debt.
    "aggressive": """Ticker,Category,Value,Units
HDFC Flexi Cap Fund,Flexi Cap Equity,180000,94.54
Nippon Small Cap Fund,Small Cap Equity,150000,833.33
Kotak Emerging Equity Fund,Mid Cap Equity,130000,1083.33
Motilal Oswal Nasdaq 100 FOF,International Equity,90000,2250
HDFC Short Term Debt Fund,Short Duration Debt,50000,1694.92""",
    # Exaggerated idle-cash story ~₹5.5L — ~90% liquid / overnight.
    "idle_cash": """Ticker,Category,Value,Units
ICICI Pru Liquid Fund,Liquid,350000,933.33
SBI Overnight Fund,Overnight,150000,125
HDFC Flexi Cap Fund,Flexi Cap Equity,50000,26.26""",
    # First-timer ~₹35k — 2 funds: index equity + liquid.
    "beginner": """Ticker,Category,Value,Units
UTI Nifty 50 Index Fund,Index Equity,25000,192.31
ICICI Pru Liquid Fund,Liquid,10000,26.67""",
}


@router.post("/portfolio")
async def analyze_portfolio_endpoint(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
):
    """Upload a portfolio CSV and get AI-powered analysis."""
    # 1. File size limit - potential DoS vector
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES / (1024*1024):.1f}MB"
        )

    # 2. CSV parsing with try-except - malformed input returns 500
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV format: {str(e)}"
        )

    # 3. Column validation - verify required columns exist
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing_columns)}. Required: {', '.join(REQUIRED_COLUMNS)}"
        )

    portfolio_data = df.to_dict(orient="records")

    # 4. Invalid language codes return 500 instead of 400
    try:
        lang = Language(language)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language code: '{language}'. Supported: en, hi, mr, ta, bn"
        )

    result = await analyze_portfolio(portfolio_data, lang)
    return result


@router.get("/portfolio/sample")
async def get_sample_portfolio(variant: str = "balanced"):
    """Get a sample portfolio CSV for testing.

    `variant` selects one of the SAMPLE_PORTFOLIOS. An unknown variant falls
    back to `balanced` so a typo never breaks the on-stage demo flow.
    """
    csv_content = SAMPLE_PORTFOLIOS.get(variant, SAMPLE_PORTFOLIOS["balanced"])

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_portfolio.csv"'}
    )


@router.get("/portfolio/cas-sample")
async def get_cas_sample(language: str = "en"):
    """Analyze the bundled synthetic sample CAS (WEA-73).

    De-scoped, demo-safe slice: runs the exact same orchestrator the CSV path
    uses on a KNOWN, hardcoded set of holdings (SAMPLE_CAS_HOLDINGS) — no live
    PDF parsing, so the on-stage flow cannot fail. Returns the analysis plus the
    holdings so the frontend can render the allocation chart without parsing PDF.
    """
    # Validate language → 400 on bad code (mirrors the CSV endpoint).
    try:
        lang = Language(language)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language code: '{language}'. Supported: en, hi, mr, ta, bn"
        )

    result = await analyze_portfolio(SAMPLE_CAS_HOLDINGS, lang)
    return {"analysis": result, "holdings": SAMPLE_CAS_HOLDINGS}


@router.get("/portfolio/cas-sample/pdf")
async def get_cas_sample_pdf():
    """Serve the bundled synthetic sample CAS PDF so judges can open it."""
    if not os.path.exists(SAMPLE_CAS_PDF_PATH):
        raise HTTPException(status_code=404, detail="Sample CAS PDF not found.")
    return FileResponse(
        SAMPLE_CAS_PDF_PATH,
        media_type="application/pdf",
        filename="sample_cas.pdf",
        content_disposition_type="inline",
    )
