from fastapi import APIRouter
from models.schemas import RiskProfileRequest, RiskProfileResponse
from services.risk_service import score_quiz, ALLOCATIONS
from services.claude_service import generate_goal_plan

router = APIRouter()


@router.post("/risk-profile", response_model=RiskProfileResponse)
async def get_risk_profile(req: RiskProfileRequest):
    """Score risk quiz and return profile with recommended allocation."""
    profile, score = score_quiz(req.answers)
    allocation = ALLOCATIONS[profile]

    explanations = {
        "conservative": "You prefer capital preservation. We recommend low-risk debt instruments.",
        "moderate": "You seek balanced growth. A mix of equity and debt suits your profile.",
        "aggressive": "You aim for maximum growth. Higher equity allocation matches your risk appetite.",
    }

    return RiskProfileResponse(
        profile=profile,
        score=score,
        explanation=explanations[profile.value],
        recommended_allocation=allocation,
    )
