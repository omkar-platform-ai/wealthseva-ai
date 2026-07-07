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


# ---------------------------------------------------------------------------
# Localized prose templates.
# Placeholders are filled from the computed values dict in _render().
# Financial product names (SIP, liquid/equity/debt fund) are transliterated as
# is common in Indian vernacular finance; proper-noun fund/goal names ({name})
# pass through unchanged. Format specs (:,.0f / :,.1f) match the EN originals.
# ---------------------------------------------------------------------------
NUDGE_TEXT = {
    Language.EN: {
        "idle_cash": {
            "title": "₹{excess:,.0f} sitting idle above your emergency corpus",
            "body": (
                "Your liquid fund (₹{liquid_value:,.0f}) covers your "
                "{months}-month emergency corpus (₹{emergency_needed:,.0f}) "
                "with ₹{excess:,.0f} to spare. That excess is earning "
                "~{return_pct:.1f}% p.a. — it could work harder in a "
                "diversified equity or short-duration debt fund."
            ),
            "data_points": [
                "Liquid fund ({name}): ₹{liquid_value:,.0f}",
                "Monthly expenses (from bank transactions): ₹{monthly_expenses:,}",
                "Emergency corpus = {months} months × ₹{monthly_expenses:,} = ₹{emergency_needed:,.0f}",
            ],
            "rule": "Liquid fund > emergency corpus × 1.3 → idle-cash nudge",
            "calculation": "₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} excess",
            "chat_seed": (
                "I have ₹{excess:,.0f} above my emergency corpus sitting in the liquid fund. "
                "Where should I invest it to earn better returns?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP is ₹{shortfall:,.0f}/month below target",
            "body": (
                "To reach ₹{target:,.0f} by {date}, you need "
                "₹{required:,.0f}/month at 12% p.a. Your current SIP is "
                "₹{actual:,.0f} — a ₹{shortfall:,.0f}/month gap that "
                "compounds over {months} months."
            ),
            "data_points": [
                "Goal: {name} — target ₹{target:,.0f} by {date}",
                "Current savings ₹{current:,.0f} grows to ₹{fv_current:,.0f} at 12% p.a.",
                "Remaining to fund via SIP: ₹{remaining:,.0f} over {months} months",
            ],
            "rule": "Required SIP > actual SIP by >{pct:.0f}% → SIP-shortfall nudge",
            "calculation": (
                "Required: ₹{required:,.0f}/month · "
                "Actual: ₹{actual:,.0f}/month · "
                "Gap: ₹{shortfall:,.0f}/month"
            ),
            "chat_seed": (
                "My {name} goal needs ₹{required:,.0f}/month but I'm only investing "
                "₹{actual:,.0f}. How do I close the ₹{shortfall:,.0f} monthly gap?"
            ),
        },
    },
    Language.HI: {
        "idle_cash": {
            "title": "आपातकालीन निधि से ऊपर ₹{excess:,.0f} निष्क्रिय खड़े हैं",
            "body": (
                "आपका लिक्विड फंड (₹{liquid_value:,.0f}) आपके {months}-माह के आपातकालीन निधि "
                "(₹{emergency_needed:,.0f}) को कवर करता है और ₹{excess:,.0f} अतिरिक्त हैं। "
                "यह राशि ~{return_pct:.1f}% प्रति वर्ष कमा रही है — डायवर्सिफाइड इक्विटी या "
                "शॉर्ट-ड्यूरेशन डेट फंड में बेहतर रिटर्न दे सकती है।"
            ),
            "data_points": [
                "लिक्विड फंड ({name}): ₹{liquid_value:,.0f}",
                "मासिक खर्च (बैंक लेन-देन से): ₹{monthly_expenses:,}",
                "आपातकालीन निधि = {months} माह × ₹{monthly_expenses:,} = ₹{emergency_needed:,.0f}",
            ],
            "rule": "लिक्विड फंड > आपातकालीन निधि × 1.3 → निष्क्रिय-राशि नज़रअंदाज़",
            "calculation": "₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} अतिरिक्त",
            "chat_seed": (
                "मेरे पास आपातकालीन निधि से ₹{excess:,.0f} ऊपर लिक्विड फंड में खड़े हैं। "
                "बेहतर रिटर्न के लिए मैं इसे कहाँ निवेश करूँ?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP लक्ष्य से ₹{shortfall:,.0f}/माह पीछे है",
            "body": (
                "{date} तक ₹{target:,.0f} तक पहुँचने के लिए आपको 12% प्रति वर्ष पर "
                "₹{required:,.0f}/माह चाहिए। आपका मौजूदा SIP ₹{actual:,.0f} है — "
                "₹{shortfall:,.0f}/माह का अंतर {months} महीनों में चक्रवृद्धि होगा।"
            ),
            "data_points": [
                "लक्ष्य: {name} — लक्ष्य राशि ₹{target:,.0f}, तिथि {date}",
                "मौजूदा बचत ₹{current:,.0f}, 12% प्रति वर्ष पर बढ़कर ₹{fv_current:,.0f}",
                "SIP से जुटाने बाकी: ₹{remaining:,.0f}, {months} माह में",
            ],
            "rule": "आवश्यक SIP > वास्तविक SIP से >{pct:.0f}% → SIP-कमी सूचना",
            "calculation": (
                "आवश्यक: ₹{required:,.0f}/माह · "
                "वास्तविक: ₹{actual:,.0f}/माह · "
                "अंतर: ₹{shortfall:,.0f}/माह"
            ),
            "chat_seed": (
                "मेरे {name} लक्ष्य को ₹{required:,.0f}/माह चाहिए, लेकिन मैं केवल "
                "₹{actual:,.0f} निवेश कर रहा हूँ। ₹{shortfall:,.0f}/माह का अंतर मैं कैसे पूरा करूँ?"
            ),
        },
    },
    Language.MR: {
        "idle_cash": {
            "title": "आपत्कालीन निधीपेक्षा वर ₹{excess:,.0f} निष्क्रिय आहेत",
            "body": (
                "तुमचा लिक्विड फंड (₹{liquid_value:,.0f}) तुमच्या {months}-महिन्यांच्या "
                "आपत्कालीन निधीला (₹{emergency_needed:,.0f}) व्यापतो आणि ₹{excess:,.0f} अतिरिक्त आहेत. "
                "ही रक्कम ~{return_pct:.1f}% दरवर्षी कमवत आहे — डायव्हर्सिफाइड इक्विटी किंवा "
                "शॉर्ट-ड्युरेशन डेट फंडमध्ये ती अधिक परतावा देऊ शकते."
            ),
            "data_points": [
                "लिक्विड फंड ({name}): ₹{liquid_value:,.0f}",
                "मासिक खर्च (बँक व्यवहारांवरून): ₹{monthly_expenses:,}",
                "आपत्कालीन निधी = {months} महिने × ₹{monthly_expenses:,} = ₹{emergency_needed:,.0f}",
            ],
            "rule": "लिक्विड फंड > आपत्कालीन निधी × 1.3 → निष्क्रिय-रक्कम सूचना",
            "calculation": "₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} अतिरिक्त",
            "chat_seed": (
                "माझ्याकडे आपत्कालीन निधीपेक्षा ₹{excess:,.0f} जास्त लिक्विड फंडमध्ये आहे. "
                "चांगला परतावा मिळवण्यासाठी मी हे कुठे गुंतवावे?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP लक्ष्यापेक्षा ₹{shortfall:,.0f}/महिना मागे आहे",
            "body": (
                "{date} पर्यंत ₹{target:,.0f} पर्यंत पोहोचण्यासाठी तुम्हाला 12% दरवर्षी "
                "₹{required:,.0f}/महिना लागेल. तुमचा सध्याचा SIP ₹{actual:,.0f} आहे — "
                "₹{shortfall:,.0f}/महिनाचा फरक {months} महिन्यांत चक्रवाढ होईल."
            ),
            "data_points": [
                "लक्ष्य: {name} — लक्ष्य रक्कम ₹{target:,.0f}, तारीख {date}",
                "सध्याची बचत ₹{current:,.0f}, 12% दरवर्षी वाढून ₹{fv_current:,.0f}",
                "SIP ने उभारायची रक्कम: ₹{remaining:,.0f}, {months} महिन्यांत",
            ],
            "rule": "आवश्यक SIP > वास्तविक SIP पेक्षा >{pct:.0f}% → SIP-कमतरता सूचना",
            "calculation": (
                "आवश्यक: ₹{required:,.0f}/महिना · "
                "वास्तविक: ₹{actual:,.0f}/महिना · "
                "फरक: ₹{shortfall:,.0f}/महिना"
            ),
            "chat_seed": (
                "माझ्या {name} लक्ष्याला ₹{required:,.0f}/महिना लागतो, पण मी फक्त "
                "₹{actual:,.0f} गुंतवत आहे. ₹{shortfall:,.0f}/महिनाचा फरक मी कसा भरून काढू?"
            ),
        },
    },
    Language.TA: {
        "idle_cash": {
            "title": "அவசரநிதியை விட ₹{excess:,.0f} செயலின்றி உள்ளது",
            "body": (
                "உங்கள் லிக்விட் ஃபண்டு (₹{liquid_value:,.0f}) உங்கள் {months}-மாத "
                "அவசரநிதியை (₹{emergency_needed:,.0f}) வரவேற்கிறது, ₹{excess:,.0f} மிகையாக உள்ளது. "
                "இது ~{return_pct:.1f}% ஆண்டு வருமானம் ஈட்டுகிறது — டைவர்சிஃபைடு ஈக்விட்டி அல்லது "
                "ஷார்ட்-டியூரேஷன் டெப்ட் ஃபண்டில் மேலும் வருவாய் தரலாம்."
            ),
            "data_points": [
                "லிக்விட் ஃபண்டு ({name}): ₹{liquid_value:,.0f}",
                "மாதாந்திர செலவுகள் (வங்கி பரிவர்த்தனைகளிலிருந்து): ₹{monthly_expenses:,}",
                "அவசரநிதி = {months} மாதம் × ₹{monthly_expenses:,} = ₹{emergency_needed:,.0f}",
            ],
            "rule": "லிக்விட் ஃபண்டு > அவசரநிதி × 1.3 → செயலின்மை-பணம் அறிவுறுத்தல்",
            "calculation": "₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} மிகை",
            "chat_seed": (
                "என்னிடம் அவசரநிதியை விட ₹{excess:,.0f} அதிகமாக லிக்விட் ஃபண்டில் உள்ளது. "
                "சிறந்த வருவாய்க்கு இதை எங்கு முதலீடு செய்யலாம்?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP இலக்கை விட ₹{shortfall:,.0f}/மாதம் பின்தங்கி உள்ளது",
            "body": (
                "{date} க்குள் ₹{target:,.0f} அடைய 12% ஆண்டு வீதத்தில் ₹{required:,.0f}/மாதம் தேவை. "
                "உங்கள் தற்போதைய SIP ₹{actual:,.0f} — ₹{shortfall:,.0f}/மாத இடைவெளி "
                "{months} மாதங்களில் கூட்டுவட்டியாகும்."
            ),
            "data_points": [
                "இலக்கு: {name} — இலக்கு தொகை ₹{target:,.0f}, தேதி {date}",
                "தற்போதைய சேமிப்பு ₹{current:,.0f}, 12% ஆண்டு வீதத்தில் ₹{fv_current:,.0f} ஆகும்",
                "SIP மூலம் திரட்ட வேண்டியது: ₹{remaining:,.0f}, {months} மாதங்களில்",
            ],
            "rule": "தேவையான SIP > உண்மையான SIP ஐ விட >{pct:.0f}% → SIP-குறைவு அறிவுறுத்தல்",
            "calculation": (
                "தேவை: ₹{required:,.0f}/மாதம் · "
                "உண்மையானது: ₹{actual:,.0f}/மாதம் · "
                "இடைவெளி: ₹{shortfall:,.0f}/மாதம்"
            ),
            "chat_seed": (
                "எனது {name} இலக்கிற்கு ₹{required:,.0f}/மாதம் தேவை, ஆனால் நான் ₹{actual:,.0f} மட்டுமே "
                "முதலீடு செய்கிறேன். ₹{shortfall:,.0f}/மாத இடைவெளியை எப்படி நிரப்புவது?"
            ),
        },
    },
    Language.BN: {
        "idle_cash": {
            "title": "জরুরি তহবিলের ওপর ₹{excess:,.0f} নিষ্ক্রিয় পড়ে আছে",
            "body": (
                "আপনার লিকুইড ফান্ড (₹{liquid_value:,.0f}) আপনার {months}-মাসের জরুরি তহবিল "
                "(₹{emergency_needed:,.0f}) ঢেকে রাখে এবং ₹{excess:,.0f} অতিরিক্ত আছে। "
                "এই অংক ~{return_pct:.1f}% বার্ষিক আয় করছে — ডাইভার্সিফাইড ইকুইটি বা "
                "শর্ট-ডিউরেশন ডেট ফান্ডে এটি বেশি লাভ দিতে পারে।"
            ),
            "data_points": [
                "লিকুইড ফান্ড ({name}): ₹{liquid_value:,.0f}",
                "মাসিক খরচ (ব্যাংক লেনদেন থেকে): ₹{monthly_expenses:,}",
                "জরুরি তহবিল = {months} মাস × ₹{monthly_expenses:,} = ₹{emergency_needed:,.0f}",
            ],
            "rule": "লিকুইড ফান্ড > জরুরি তহবিল × 1.3 → নিষ্ক্রিয়-অর্থ বার্তা",
            "calculation": "₹{liquid_value:,.0f} − ₹{emergency_needed:,.0f} = ₹{excess:,.0f} অতিরিক্ত",
            "chat_seed": (
                "আমার জরুরি তহবিলের চেয়ে ₹{excess:,.0f} বেশি লিকুইড ফান্ডে পড়ে আছে। "
                "ভালো লাভের জন্য এটি কোথায় বিনিয়োগ করব?"
            ),
        },
        "sip_shortfall": {
            "title": "{name} SIP লক্ষ্যের চেয়ে ₹{shortfall:,.0f}/মাস পিছিয়ে আছে",
            "body": (
                "{date} এর মধ্যে ₹{target:,.0f} ছুঁতে 12% বার্ষিক হারে ₹{required:,.0f}/মাস দরকার। "
                "আপনার বর্তমান SIP ₹{actual:,.0f} — ₹{shortfall:,.0f}/মাস ঘাটতি "
                "{months} মাসে চক্রবৃদ্ধি হবে।"
            ),
            "data_points": [
                "লক্ষ্য: {name} — লক্ষ্য অঙ্ক ₹{target:,.0f}, তারিখ {date}",
                "বর্তমান সঞ্চয় ₹{current:,.0f}, 12% বার্ষিক হারে বেড়ে ₹{fv_current:,.0f}",
                "SIP দিয়ে গাঁথতে বাকি: ₹{remaining:,.0f}, {months} মাসে",
            ],
            "rule": "প্রয়োজনীয় SIP > প্রকৃত SIP থেকে >{pct:.0f}% → SIP-ঘাটতি বার্তা",
            "calculation": (
                "প্রয়োজন: ₹{required:,.0f}/মাস · "
                "প্রকৃত: ₹{actual:,.0f}/মাস · "
                "ঘাটতি: ₹{shortfall:,.0f}/মাস"
            ),
            "chat_seed": (
                "আমার {name} লক্ষ্যে ₹{required:,.0f}/মাস দরকার, কিন্তু আমি মাত্র ₹{actual:,.0f} "
                "বিনিয়োগ করছি। ₹{shortfall:,.0f}/মাস ঘাটতি কীভাবে পূরণ করব?"
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
        "excess": excess,
        "liquid_value": liquid_value,
        "emergency_needed": emergency_needed,
        "months": _EMERGENCY_MONTHS,
        "monthly_expenses": _MONTHLY_EXPENSES,
        "return_pct": liquid.get("gain_loss_pct", 7.0),
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
            "target": target,
            "date": g["target_date"][:7],
            "required": required_sip,
            "actual": actual_sip,
            "shortfall": shortfall,
            "months": months,
            "current": current,
            "fv_current": fv_current,
            "remaining": remaining,
            "pct": _SIP_SHORTFALL_PCT * 100,
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
