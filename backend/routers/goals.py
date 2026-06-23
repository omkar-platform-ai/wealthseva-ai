from fastapi import APIRouter
from models.schemas import GoalRequest, GoalResponse
from services.claude_service import generate_goal_plan

router = APIRouter()


@router.post("/goals", response_model=GoalResponse)
async def create_goal_plan(req: GoalRequest):
    """Generate a savings and investment plan for user's financial goals."""
    goals_list = [g.model_dump() for g in req.goals]
    plan = await generate_goal_plan(goals_list, req.language)

    total_monthly = sum(g.monthly_contribution for g in req.goals)
    return GoalResponse(
        goals=goals_list,
        summary=plan,
        total_monthly_required=total_monthly,
    )
