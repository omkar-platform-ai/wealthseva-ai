from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class Language(str, Enum):
    EN = "en"
    HI = "hi"
    MR = "mr"
    TA = "ta"
    BN = "bn"


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    language: Language = Language.EN
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    language: Language
    detected_language: Optional[Language] = None


class RiskQuizAnswer(BaseModel):
    question_id: int
    answer: str


class RiskProfileRequest(BaseModel):
    answers: List[RiskQuizAnswer]
    language: Language = Language.EN


class RiskProfileResponse(BaseModel):
    profile: RiskProfile
    score: int
    explanation: str
    recommended_allocation: dict


class Goal(BaseModel):
    name: str
    target_amount: float
    target_date: str  # ISO date string
    current_savings: float = 0.0
    monthly_contribution: float = 0.0


class GoalRequest(BaseModel):
    goals: List[Goal]
    language: Language = Language.EN


class GoalResponse(BaseModel):
    goals: List[dict]
    summary: str
    total_monthly_required: float
