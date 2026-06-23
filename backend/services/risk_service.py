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

ALLOCATIONS = {
    RiskProfile.CONSERVATIVE: {"FD/Bonds": 70, "Debt MF": 20, "Equity MF": 10},
    RiskProfile.MODERATE: {"FD/Bonds": 30, "Debt MF": 30, "Equity MF": 40},
    RiskProfile.AGGRESSIVE: {"FD/Bonds": 10, "Debt MF": 10, "Equity MF": 80},
}


def score_quiz(answers: list[RiskQuizAnswer]) -> tuple[RiskProfile, int]:
    """Score quiz answers and return a risk profile + numeric score."""
    total = sum(answer.answer == "D" and 4 or
                answer.answer == "C" and 3 or
                answer.answer == "B" and 2 or 1
                for answer in answers)

    if total <= 8:
        return RiskProfile.CONSERVATIVE, total
    elif total <= 14:
        return RiskProfile.MODERATE, total
    else:
        return RiskProfile.AGGRESSIVE, total
