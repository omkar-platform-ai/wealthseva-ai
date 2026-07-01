from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from models.schemas import Language
from services.claude_service import analyze_portfolio
import pandas as pd
import io

router = APIRouter()

# Security limits
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
REQUIRED_COLUMNS = {"Ticker", "Category", "Value", "Units"}


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
async def get_sample_portfolio():
    """Get a sample portfolio CSV for testing."""
    csv_content = """Ticker,Category,Value,Units
HDFC Top 100,Large Cap Equity,50000,120
ICICI Prudential Gilt,Debt,30000,450
SBI Liquid Fund,Liquid,20000,200"""

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sample_portfolio.csv"'}
    )
