from pydantic import BaseModel, model_validator
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

    @model_validator(mode='after')
    def validate_answers_count(self):
        if len(self.answers) != 5:
            raise ValueError("Exactly 5 answers required")
        return self


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


class PortfolioHolding(BaseModel):
    isin: str
    name: str
    category: str
    units: float
    nav: float
    current_value: float
    gain_loss_pct: float


class IDBIPortfolioResponse(BaseModel):
    data: List[PortfolioHolding]
    source: str


class IDBIRiskProfileResponse(BaseModel):
    data: dict
    source: str


class IDBIGoal(BaseModel):
    id: str
    name: str
    target_amount: float
    target_date: str
    current_savings: float
    monthly_sip: float
    progress_pct: float


class IDBIGoalsResponse(BaseModel):
    data: List[IDBIGoal]
    source: str
