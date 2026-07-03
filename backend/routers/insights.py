from fastapi import APIRouter, Query
from models.schemas import Language
from services.claude_service import generate_market_insights

router = APIRouter()


@router.get("/insights")
async def get_insights(language: Language = Query(default=Language.EN)):
    """Get daily AI-generated market insights in the user's language."""
    insights = await generate_market_insights(language)
    return {"insights": insights, "language": language.value}
