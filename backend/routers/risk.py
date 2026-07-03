from fastapi import APIRouter
from models.schemas import RiskProfileRequest, RiskProfileResponse, RiskTrace
from services.risk_service import score_quiz, answer_points, ALLOCATIONS, SCORE_BANDS
from services.claude_service import generate_risk_explanation

router = APIRouter()


@router.post("/risk-profile", response_model=RiskProfileResponse)
async def get_risk_profile(req: RiskProfileRequest):
    """Score risk quiz and return profile with recommended allocation."""
    profile, score = score_quiz(req.answers)
    allocation = ALLOCATIONS[profile]

    # Generate explanation using Claude service
    explanation = await generate_risk_explanation(profile.value, score, allocation, req.language)

    trace = RiskTrace(
        answer_points=answer_points(req.answers),
        score=score,
        max_score=20,
        bands={p.value: list(band) for p, band in SCORE_BANDS.items()},
    )

    return RiskProfileResponse(
        profile=profile,
        score=score,
        explanation=explanation,
        recommended_allocation=allocation,
        trace=trace,
    )
