from fastapi import APIRouter
from datetime import date
from models.schemas import GoalRequest, GoalResponse
from services.claude_service import generate_goal_plan

router = APIRouter()

PRESETS = [
    {"id": "retirement", "label_key": "preset_retirement", "target_amount": 10000000, "years": 25, "icon": "🏖️"},
    {"id": "house", "label_key": "preset_house", "target_amount": 5000000, "years": 10, "icon": "🏠"},
    {"id": "education", "label_key": "preset_education", "target_amount": 2500000, "years": 8, "icon": "🎓"},
    {"id": "wedding", "label_key": "preset_wedding", "target_amount": 1500000, "years": 3, "icon": "💍"},
]


@router.get("/goals/presets")
async def get_goal_presets():
    return {"presets": PRESETS}


def _compute_projection(target_amount: float, current_savings: float, target_date: str) -> dict:
    today = date.today()
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return {"monthly_sip": 0, "projected_corpus": int(target_amount), "yearly_data": []}

    months = max(1, (target.year - today.year) * 12 + (target.month - today.month))
    r = 0.01  # 1% per month → 12% p.a.

    fv_savings = current_savings * (1 + r) ** months
    remaining = target_amount - fv_savings
    sip = remaining * r / ((1 + r) ** months - 1) if remaining > 0 else 0.0

    yearly_data = []
    for y in range(1, (months // 12) + 1):
        m = y * 12
        corpus = current_savings * (1 + r) ** m
        if sip > 0:
            corpus += sip * ((1 + r) ** m - 1) / r
        yearly_data.append({"year": y, "corpus": round(corpus)})

    projected = fv_savings + (sip * ((1 + r) ** months - 1) / r if sip > 0 else 0)
    return {
        "monthly_sip": round(sip),
        "projected_corpus": round(projected),
        "yearly_data": yearly_data,
    }


@router.post("/goals", response_model=GoalResponse)
async def create_goal_plan(req: GoalRequest):
    goals_list = [g.model_dump() for g in req.goals]
    plan = await generate_goal_plan(goals_list, req.language)

    projections = []
    for g in req.goals:
        proj = _compute_projection(g.target_amount, g.current_savings, g.target_date)
        projections.append({"name": g.name, "target_amount": g.target_amount, **proj})

    total_monthly = sum(p["monthly_sip"] for p in projections)
    return GoalResponse(
        goals=goals_list,
        projections=projections,
        summary=plan,
        total_monthly_required=total_monthly,
    )
