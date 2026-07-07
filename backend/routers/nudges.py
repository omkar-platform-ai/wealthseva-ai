"""
Money Moments nudge engine — deterministic rules over IDBI sandbox data.
No LLM is involved; every figure is arithmetic-only (coherent with RiskTrace/GoalTrace).

Prose (title/body/why_trace/chat_seed) is localized per request via NUDGE_TEXT;
the underlying figures are identical across locales.
"""
import asyncio
from datetime import date
from typing import Optional
from fastapi import APIRouter, Query
from models.schemas import Language, Nudge, NudgeType, NudgeWhyTrace, NudgesResponse
from routers.idbi import get_portfolio, get_goals

router = APIRouter()

_MONTHLY_RATE = 0.01          # 12% p.a. assumed for equity/diversified funds
_EMERGENCY_MONTHS = 6
_MONTHLY_EXPENSES = 28_200    # derived from MOCK_TRANSACTIONS in idbi.py
_SIP_DRIFT_FLOOR = 12         # months — skip goals too close to adjust via SIP
_SIP_SHORTFALL_PCT = 0.10     # 10% below required → fire nudge


def _fv_factor(months: int) -> float:
    r = _MONTHLY_RATE
    return ((1 + r) ** months - 1) / r


def _fv_lump(amount: float, months: int) -> float:
    return amount * (1 + _MONTHLY_RATE) ** months


def _months_remaining(target_date_str: str) -> int:
    target = date.fromisoformat(target_date_str)
    today = date.today()
    return max(0, (target.year - today.year) * 12 + (target.month - today.month))


def _indian(amount: float) -> str:
    """Format a rupee amount with Indian lakh/crore grouping, no decimals.

    240000 -> "2,40,000", 169200 -> "1,69,200", 2500000 -> "25,00,000",
    70800 -> "70,800", 885 -> "885". Matches how IDBI/Indian bank statements
    display amounts, instead of the Western "240,000".
    """
    n = int(round(amount))
    sign = "-" if n < 0 else ""
    digits = str(abs(n))
    if len(digits) <= 3:
        return sign + digits
    last3, rest = digits[-3:], digits[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return sign + ",".join(groups) + "," + last3


# ---------------------------------------------------------------------------
# Localized prose templates.
# Placeholders are filled (bare {name}, no format specs) from the values dict
# built in _idle_cash_nudge / _sip_shortfall_nudge. Rupee amounts are pre-formatted
# via _indian() so figures use Indian lakh/crore grouping in every locale.
# Financial product names (SIP, liquid/equity/debt fund) are transliterated as
# is common in Indian vernacular finance; proper-noun fund/goal names ({name})
# pass through unchanged.
# ---------------------------------------------------------------------------
NUDGE_TEXT = {
    Language.EN: {
        "idle_cash": {
            "title": "₹{excess} sitting idle above your emergency corpus",
            "body": (
                "Your liquid fund (₹{liquid_value}) covers your "
                "{months}-month emergency corpus (₹{emergency_needed}) "
                "with ₹{excess} to spare. That excess is earning "
                "~{return_pct}% p.a. — it could work harder in a "
                "diversified equity or short-duration debt fund."
            ),
            "data_points": [
                "Liquid fund ({name}): ₹{liquid_value}",
                "Monthly expenses (from bank transactions): ₹{monthly_expenses}",
                "Emergency corpus = {months} months × ₹{monthly_expenses} = ₹{emergency_needed}",
            ],
            "rule": "Liquid fund > emergency corpus × 1.3 → idle-cash nudge",
            "calculation": "₹{liquid_value} − ₹{emergency_needed} = ₹{excess} excess",
            "chat_seed": (
                "I have ₹{excess} above my emergency corpus sitting in the liquid fund. "
                "Where should I invest it to earn better returns?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP is ₹{shortfall}/month below target",
            "body": (
                "To reach ₹{target} by {date}, you need "
                "₹{required}/month at 12% p.a. Your current SIP is "
                "₹{actual} — a ₹{shortfall}/month gap that "
                "compounds over {months} months."
            ),
            "data_points": [
                "Goal: {name} — target ₹{target} by {date}",
                "Current savings ₹{current} grows to ₹{fv_current} at 12% p.a.",
                "Remaining to fund via SIP: ₹{remaining} over {months} months",
            ],
            "rule": "Required SIP > actual SIP by >{pct}% → SIP-shortfall nudge",
            "calculation": (
                "Required: ₹{required}/month · "
                "Actual: ₹{actual}/month · "
                "Gap: ₹{shortfall}/month"
            ),
            "chat_seed": (
                "My {name} goal needs ₹{required}/month but I'm only investing "
                "₹{actual}. How do I close the ₹{shortfall} monthly gap?"
            ),
        },
    },
    Language.HI: {
        "idle_cash": {
            "title": "आपातकालीन निधि से ऊपर ₹{excess} निष्क्रिय खड़े हैं",
            "body": (
                "आपका लिक्विड फंड (₹{liquid_value}) आपके {months}-माह के आपातकालीन निधि "
                "(₹{emergency_needed}) को कवर करता है और ₹{excess} अतिरिक्त हैं। "
                "यह राशि ~{return_pct}% प्रति वर्ष कमा रही है — डायवर्सिफाइड इक्विटी या "
                "शॉर्ट-ड्यूरेशन डेट फंड में बेहतर रिटर्न दे सकती है।"
            ),
            "data_points": [
                "लिक्विड फंड ({name}): ₹{liquid_value}",
                "मासिक खर्च (बैंक लेन-देन से): ₹{monthly_expenses}",
                "आपातकालीन निधि = {months} माह × ₹{monthly_expenses} = ₹{emergency_needed}",
            ],
            "rule": "लिक्विड फंड > आपातकालीन निधि × 1.3 → निष्क्रिय-राशि नज़रअंदाज़",
            "calculation": "₹{liquid_value} − ₹{emergency_needed} = ₹{excess} अतिरिक्त",
            "chat_seed": (
                "मेरे पास आपातकालीन निधि से ₹{excess} ऊपर लिक्विड फंड में खड़े हैं। "
                "बेहतर रिटर्न के लिए मैं इसे कहाँ निवेश करूँ?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP लक्ष्य से ₹{shortfall}/माह पीछे है",
            "body": (
                "{date} तक ₹{target} तक पहुँचने के लिए आपको 12% प्रति वर्ष पर "
                "₹{required}/माह चाहिए। आपका मौजूदा SIP ₹{actual} है — "
                "₹{shortfall}/माह का अंतर {months} महीनों में चक्रवृद्धि होगा।"
            ),
            "data_points": [
                "लक्ष्य: {name} — लक्ष्य राशि ₹{target}, तिथि {date}",
                "मौजूदा बचत ₹{current}, 12% प्रति वर्ष पर बढ़कर ₹{fv_current}",
                "SIP से जुटाने बाकी: ₹{remaining}, {months} माह में",
            ],
            "rule": "आवश्यक SIP > वास्तविक SIP से >{pct}% → SIP-कमी सूचना",
            "calculation": (
                "आवश्यक: ₹{required}/माह · "
                "वास्तविक: ₹{actual}/माह · "
                "अंतर: ₹{shortfall}/माह"
            ),
            "chat_seed": (
                "मेरे {name} लक्ष्य को ₹{required}/माह चाहिए, लेकिन मैं केवल "
                "₹{actual} निवेश कर रहा हूँ। ₹{shortfall}/माह का अंतर मैं कैसे पूरा करूँ?"
            ),
        },
    },
    Language.MR: {
        "idle_cash": {
            "title": "आपत्कालीन निधीपेक्षा वर ₹{excess} निष्क्रिय आहेत",
            "body": (
                "तुमचा लिक्विड फंड (₹{liquid_value}) तुमच्या {months}-महिन्यांच्या "
                "आपत्कालीन निधीला (₹{emergency_needed}) व्यापतो आणि ₹{excess} अतिरिक्त आहेत. "
                "ही रक्कम ~{return_pct}% दरवर्षी कमवत आहे — डायव्हर्सिफाइड इक्विटी किंवा "
                "शॉर्ट-ड्युरेशन डेट फंडमध्ये ती अधिक परतावा देऊ शकते."
            ),
            "data_points": [
                "लिक्विड फंड ({name}): ₹{liquid_value}",
                "मासिक खर्च (बँक व्यवहारांवरून): ₹{monthly_expenses}",
                "आपत्कालीन निधी = {months} महिने × ₹{monthly_expenses} = ₹{emergency_needed}",
            ],
            "rule": "लिक्विड फंड > आपत्कालीन निधी × 1.3 → निष्क्रिय-रक्कम सूचना",
            "calculation": "₹{liquid_value} − ₹{emergency_needed} = ₹{excess} अतिरिक्त",
            "chat_seed": (
                "माझ्याकडे आपत्कालीन निधीपेक्षा ₹{excess} जास्त लिक्विड फंडमध्ये आहे. "
                "चांगला परतावा मिळवण्यासाठी मी हे कुठे गुंतवावे?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP लक्ष्यापेक्षा ₹{shortfall}/महिना मागे आहे",
            "body": (
                "{date} पर्यंत ₹{target} पर्यंत पोहोचण्यासाठी तुम्हाला 12% दरवर्षी "
                "₹{required}/महिना लागेल. तुमचा सध्याचा SIP ₹{actual} आहे — "
                "₹{shortfall}/महिनाचा फरक {months} महिन्यांत चक्रवाढ होईल."
            ),
            "data_points": [
                "लक्ष्य: {name} — लक्ष्य रक्कम ₹{target}, तारीख {date}",
                "सध्याची बचत ₹{current}, 12% दरवर्षी वाढून ₹{fv_current}",
                "SIP ने उभारायची रक्कम: ₹{remaining}, {months} महिन्यांत",
            ],
            "rule": "आवश्यक SIP > वास्तविक SIP पेक्षा >{pct}% → SIP-कमतरता सूचना",
            "calculation": (
                "आवश्यक: ₹{required}/महिना · "
                "वास्तविक: ₹{actual}/महिना · "
                "फरक: ₹{shortfall}/महिना"
            ),
            "chat_seed": (
                "माझ्या {name} लक्ष्याला ₹{required}/महिना लागतो, पण मी फक्त "
                "₹{actual} गुंतवत आहे. ₹{shortfall}/महिनाचा फरक मी कसा भरून काढू?"
            ),
        },
    },
    Language.TA: {
        "idle_cash": {
            "title": "அவசரநிதியை விட ₹{excess} செயலின்றி உள்ளது",
            "body": (
                "உங்கள் லிக்விட் ஃபண்டு (₹{liquid_value}) உங்கள் {months}-மாத "
                "அவசரநிதியை (₹{emergency_needed}) வரவேற்கிறது, ₹{excess} மிகையாக உள்ளது. "
                "இது ~{return_pct}% ஆண்டு வருமானம் ஈட்டுகிறது — டைவர்சிஃபைடு ஈக்விட்டி அல்லது "
                "ஷார்ட்-டியூரேஷன் டெப்ட் ஃபண்டில் மேலும் வருவாய் தரலாம்."
            ),
            "data_points": [
                "லிக்விட் ஃபண்டு ({name}): ₹{liquid_value}",
                "மாதாந்திர செலவுகள் (வங்கி பரிவர்த்தனைகளிலிருந்து): ₹{monthly_expenses}",
                "அவசரநிதி = {months} மாதம் × ₹{monthly_expenses} = ₹{emergency_needed}",
            ],
            "rule": "லிக்விட் ஃபண்டு > அவசரநிதி × 1.3 → செயலின்மை-பணம் அறிவுறுத்தல்",
            "calculation": "₹{liquid_value} − ₹{emergency_needed} = ₹{excess} மிகை",
            "chat_seed": (
                "என்னிடம் அவசரநிதியை விட ₹{excess} அதிகமாக லிக்விட் ஃபண்டில் உள்ளது. "
                "சிறந்த வருவாய்க்கு இதை எங்கு முதலீடு செய்யலாம்?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP இலக்கை விட ₹{shortfall}/மாதம் பின்தங்கி உள்ளது",
            "body": (
                "{date} க்குள் ₹{target} அடைய 12% ஆண்டு வீதத்தில் ₹{required}/மாதம் தேவை. "
                "உங்கள் தற்போதைய SIP ₹{actual} — ₹{shortfall}/மாத இடைவெளி "
                "{months} மாதங்களில் கூட்டுவட்டியாகும்."
            ),
            "data_points": [
                "இலக்கு: {name} — இலக்கு தொகை ₹{target}, தேதி {date}",
                "தற்போதைய சேமிப்பு ₹{current}, 12% ஆண்டு வீதத்தில் ₹{fv_current} ஆகும்",
                "SIP மூலம் திரட்ட வேண்டியது: ₹{remaining}, {months} மாதங்களில்",
            ],
            "rule": "தேவையான SIP > உண்மையான SIP ஐ விட >{pct}% → SIP-குறைவு அறிவுறுத்தல்",
            "calculation": (
                "தேவை: ₹{required}/மாதம் · "
                "உண்மையானது: ₹{actual}/மாதம் · "
                "இடைவெளி: ₹{shortfall}/மாதம்"
            ),
            "chat_seed": (
                "எனது {name} இலக்கிற்கு ₹{required}/மாதம் தேவை, ஆனால் நான் ₹{actual} மட்டுமே "
                "முதலீடு செய்கிறேன். ₹{shortfall}/மாத இடைவெளியை எப்படி நிரப்புவது?"
            ),
        },
    },
    Language.BN: {
        "idle_cash": {
            "title": "জরুরি তহবিলের ওপর ₹{excess} নিষ্ক্রিয় পড়ে আছে",
            "body": (
                "আপনার লিকুইড ফান্ড (₹{liquid_value}) আপনার {months}-মাসের জরুরি তহবিল "
                "(₹{emergency_needed}) ঢেকে রাখে এবং ₹{excess} অতিরিক্ত আছে। "
                "এই অংক ~{return_pct}% বার্ষিক আয় করছে — ডাইভার্সিফাইড ইকুইটি বা "
                "শর্ট-ডিউরেশন ডেট ফান্ডে এটি বেশি লাভ দিতে পারে।"
            ),
            "data_points": [
                "লিকুইড ফান্ড ({name}): ₹{liquid_value}",
                "মাসিক খরচ (ব্যাংক লেনদেন থেকে): ₹{monthly_expenses}",
                "জরুরি তহবিল = {months} মাস × ₹{monthly_expenses} = ₹{emergency_needed}",
            ],
            "rule": "লিকুইড ফান্ড > জরুরি তহবিল × 1.3 → নিষ্ক্রিয়-অর্থ বার্তা",
            "calculation": "₹{liquid_value} − ₹{emergency_needed} = ₹{excess} অতিরিক্ত",
            "chat_seed": (
                "আমার জরুরি তহবিলের চেয়ে ₹{excess} বেশি লিকুইড ফান্ডে পড়ে আছে। "
                "ভালো লাভের জন্য এটি কোথায় বিনিয়োগ করব?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP লক্ষ্যের চেয়ে ₹{shortfall}/মাস পিছিয়ে আছে",
            "body": (
                "{date} এর মধ্যে ₹{target} ছুঁতে 12% বার্ষিক হারে ₹{required}/মাস দরকার। "
                "আপনার বর্তমান SIP ₹{actual} — ₹{shortfall}/মাস ঘাটতি "
                "{months} মাসে চক্রবৃদ্ধি হবে।"
            ),
            "data_points": [
                "লক্ষ্য: {name} — লক্ষ্য অঙ্ক ₹{target}, তারিখ {date}",
                "বর্তমান সঞ্চয় ₹{current}, 12% বার্ষিক হারে বেড়ে ₹{fv_current}",
                "SIP দিয়ে গাঁথতে বাকি: ₹{remaining}, {months} মাসে",
            ],
            "rule": "প্রয়োজনীয় SIP > প্রকৃত SIP থেকে >{pct}% → SIP-ঘাটতি বার্তা",
            "calculation": (
                "প্রয়োজন: ₹{required}/মাস · "
                "প্রকৃত: ₹{actual}/মাস · "
                "ঘাটতি: ₹{shortfall}/মাস"
            ),
            "chat_seed": (
                "আমার {name} লক্ষ্যে ₹{required}/মাস দরকার, কিন্তু আমি মাত্র ₹{actual} "
                "বিনিয়োগ করছি। ₹{shortfall}/মাস ঘাটতি কীভাবে পূরণ করব?"
            ),
        },
    },
}


def _render(key: str, language: Language, values: dict) -> dict:
    """Format the localized templates for a nudge with the computed values."""
    templates = NUDGE_TEXT.get(language, NUDGE_TEXT[Language.EN])[key]
    return {
        "title": templates["title"].format(**values),
        "body": templates["body"].format(**values),
        "data_points": [dp.format(**values) for dp in templates["data_points"]],
        "rule": templates["rule"].format(**values),
        "calculation": templates["calculation"].format(**values),
        "chat_seed": templates["chat_seed"].format(**values),
    }


def _idle_cash_nudge(portfolio: list, language: Language = Language.EN) -> Optional[Nudge]:
    liquid = next((h for h in portfolio if h.get("category") == "Liquid"), None)
    if not liquid:
        return None
    liquid_value = liquid["current_value"]
    emergency_needed = _EMERGENCY_MONTHS * _MONTHLY_EXPENSES
    excess = liquid_value - emergency_needed
    if excess <= emergency_needed * 0.30:
        return None
    txt = _render("idle_cash", language, {
        "excess": _indian(excess),
        "liquid_value": _indian(liquid_value),
        "emergency_needed": _indian(emergency_needed),
        "months": _EMERGENCY_MONTHS,
        "monthly_expenses": _indian(_MONTHLY_EXPENSES),
        "return_pct": f"{liquid.get('gain_loss_pct', 7.0):.1f}",
        "name": liquid["name"],
    })
    return Nudge(
        id="nudge-idle-cash",
        type=NudgeType.IDLE_CASH,
        title=txt["title"],
        body=txt["body"],
        severity="high",
        why_trace=NudgeWhyTrace(
            data_points=txt["data_points"],
            rule=txt["rule"],
            calculation=txt["calculation"],
        ),
        chat_seed=txt["chat_seed"],
    )


def _sip_shortfall_nudges(goals: list, language: Language = Language.EN) -> list:
    nudges = []
    for g in goals:
        months = _months_remaining(g["target_date"])
        # Skip goals too close to maturity — SIP changes won't help
        if months < _SIP_DRIFT_FLOOR:
            continue
        current = g.get("current_savings", 0.0)
        target = g["target_amount"]
        actual_sip = g.get("monthly_sip", 0.0)
        if actual_sip <= 0:
            continue
        fv_current = _fv_lump(current, months)
        remaining = target - fv_current
        if remaining <= 0:
            continue
        factor = _fv_factor(months)
        required_sip = remaining / factor
        if actual_sip >= required_sip * (1 - _SIP_SHORTFALL_PCT):
            continue
        shortfall = required_sip - actual_sip
        txt = _render("sip_shortfall", language, {
            "name": g["name"],
            "target": _indian(target),
            "date": g["target_date"][:7],
            "required": _indian(required_sip),
            "actual": _indian(actual_sip),
            "shortfall": _indian(shortfall),
            "months": months,
            "current": _indian(current),
            "fv_current": _indian(fv_current),
            "remaining": _indian(remaining),
            "pct": f"{_SIP_SHORTFALL_PCT * 100:.0f}",
        })
        nudges.append(Nudge(
            id=f"nudge-sip-{g['id']}",
            type=NudgeType.SIP_SHORTFALL,
            title=txt["title"],
            body=txt["body"],
            severity="medium",
            why_trace=NudgeWhyTrace(
                data_points=txt["data_points"],
                rule=txt["rule"],
                calculation=txt["calculation"],
            ),
            chat_seed=txt["chat_seed"],
        ))
    return nudges


@router.get("/nudges", response_model=NudgesResponse)
async def get_nudges(account_id: str = "demo", language: Language = Query(default=Language.EN)):
    """Deterministic Money Moments nudges — no LLM, bank-data-grounded.
    Prose is localized per `language`; figures are identical across locales."""
    portfolio_resp, goals_resp = await asyncio.gather(
        get_portfolio(account_id),
        get_goals(account_id),
    )
    portfolio = portfolio_resp.get("data") or []
    goals = goals_resp.get("data") or []
    # Normalise: IDBIGoal Pydantic objects → dicts
    portfolio = [h if isinstance(h, dict) else h.model_dump() for h in portfolio]
    goals = [g if isinstance(g, dict) else g.model_dump() for g in goals]

    nudges: list = []
    idle = _idle_cash_nudge(portfolio, language)
    if idle:
        nudges.append(idle)
    nudges.extend(_sip_shortfall_nudges(goals, language))

    return NudgesResponse(nudges=nudges, source=portfolio_resp.get("source", "mock"))
