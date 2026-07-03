"""
Risk profiling logic — maps quiz answers to risk profile + allocation.
"""
from models.schemas import RiskProfile, RiskQuizAnswer

RISK_QUESTIONS = [
    {
        "id": 1,
        "question": "How long can you keep your money invested without needing it?",
        "options": {
            "A": ("Less than 1 year", 1),
            "B": ("1–3 years", 2),
            "C": ("3–7 years", 3),
            "D": ("More than 7 years", 4),
        },
    },
    {
        "id": 2,
        "question": "If your investment fell 20% in one month, what would you do?",
        "options": {
            "A": ("Sell everything", 1),
            "B": ("Sell some", 2),
            "C": ("Do nothing", 3),
            "D": ("Buy more", 4),
        },
    },
    {
        "id": 3,
        "question": "What is your primary investment goal?",
        "options": {
            "A": ("Preserve capital", 1),
            "B": ("Regular income", 2),
            "C": ("Balanced growth", 3),
            "D": ("Maximum growth", 4),
        },
    },
    {
        "id": 4,
        "question": "How much of your monthly income do you save?",
        "options": {
            "A": ("Less than 10%", 1),
            "B": ("10–20%", 2),
            "C": ("20–40%", 3),
            "D": ("More than 40%", 4),
        },
    },
    {
        "id": 5,
        "question": "How familiar are you with investments like stocks, mutual funds, or ETFs?",
        "options": {
            "A": ("Not at all", 1),
            "B": ("Somewhat", 2),
            "C": ("Comfortable", 3),
            "D": ("Very experienced", 4),
        },
    },
]

# Allocations per requirements:
# Conservative (5-8): 60% debt, 30% large cap, 10% gold
# Moderate (9-13): 40% equity diversified, 40% debt, 20% balanced
# Aggressive (14-20): 70% equity, 20% mid/small cap, 10% debt
ALLOCATIONS = {
    RiskProfile.CONSERVATIVE: {"Debt": 60, "Large Cap": 30, "Gold": 10},
    RiskProfile.MODERATE: {"Equity Diversified": 40, "Debt": 40, "Balanced": 20},
    RiskProfile.AGGRESSIVE: {"Equity": 70, "Mid/Small Cap": 20, "Debt": 10},
}


ANSWER_POINTS = {"A": 1, "B": 2, "C": 3, "D": 4}

# Score bands must stay in sync with score_quiz() thresholds below.
SCORE_BANDS = {
    RiskProfile.CONSERVATIVE: (5, 8),
    RiskProfile.MODERATE: (9, 14),
    RiskProfile.AGGRESSIVE: (15, 20),
}


def answer_points(answers: list[RiskQuizAnswer]) -> list[int]:
    """Per-answer points (A=1 … D=4), unknown answers default to 1."""
    return [ANSWER_POINTS.get(a.answer, 1) for a in answers]


def score_quiz(answers: list[RiskQuizAnswer]) -> tuple[RiskProfile, int]:
    """Score quiz answers and return a risk profile + numeric score."""
    total = sum(answer_points(answers))

    if total <= 8:
        return RiskProfile.CONSERVATIVE, total
    elif total <= 14:
        return RiskProfile.MODERATE, total
    else:
        return RiskProfile.AGGRESSIVE, total
