from fastapi import APIRouter, UploadFile, File, Form
from models.schemas import Language
from services.claude_service import analyze_portfolio
import pandas as pd
import io

router = APIRouter()


@router.post("/portfolio")
async def analyze_portfolio_endpoint(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
):
    """Upload a portfolio CSV and get AI-powered analysis."""
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    portfolio_data = df.to_dict(orient="records")

    lang = Language(language)
    analysis = await analyze_portfolio(portfolio_data, lang)
    return {"analysis": analysis, "language": language}
