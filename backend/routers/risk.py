from fastapi import APIRouter
from models.schemas import RiskProfileRequest, RiskProfileResponse
from services.risk_service import score_quiz, ALLOCATIONS
from services.claude_service import generate_risk_explanation

router = APIRouter()


@router.post("/risk-profile", response_model=RiskProfileResponse)
async def get_risk_profile(req: RiskProfileRequest):
    """Score risk quiz and return profile with recommended allocation."""
    profile, score = score_quiz(req.answers)
    allocation = ALLOCATIONS[profile]

    # Generate explanation using Claude service
    explanation = await generate_risk_explanation(profile.value, score, allocation, req.language)

    return RiskProfileResponse(
        profile=profile,
        score=score,
        explanation=explanation,
        recommended_allocation=allocation,
    )
