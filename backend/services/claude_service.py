"""
Claude API service — handles all LLM calls, streaming, and tool use.

Primary inference path is Amazon Bedrock (IAM authentication). A direct
Anthropic-API path is used as a fallback ONLY when the Bedrock call raises
(demo-day insurance while Bedrock is blocked by the payment/Marketplace
issue). Setting ANTHROPIC_API_KEY enables the fallback; deleting it disables
it with no code change. See WEA-57.
"""
import os
import json
import time
import logging
from typing import AsyncIterator
import anthropic
from models.schemas import Language, ChatMessage
from services.language_service import get_system_prompt

logger = logging.getLogger("wealthseva.claude")

# Bedrock configuration (primary path)
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-south-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")

# Anthropic direct-API configuration (fallback path). Absence of the key
# disables the fallback entirely — behaviour is then unchanged from before.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL_ID = os.getenv("ANTHROPIC_MODEL_ID", "claude-sonnet-4-5-20250929")

MAX_HISTORY = 10
TIMEOUT_SECONDS = 10

# Lazy initialization with graceful fallback for missing AWS credentials
# When running on EC2/Lambda with IAM role, boto3 automatically finds credentials
# When running locally, AWS credentials must be configured in ~/.aws/credentials or env vars
try:
    import boto3
    _aws_credentials_available = True
except ImportError:
    _aws_credentials_available = False

# `client` is the Bedrock client and remains the primary path. Kept under this
# name so existing tests that patch `services.claude_service.client` still work.
if _aws_credentials_available:
    client = anthropic.AsyncAnthropicBedrock(
        aws_region=BEDROCK_REGION,
    )
else:
    client = None

# Direct Anthropic client (fallback) — only constructed when a key is present.
if ANTHROPIC_API_KEY:
    _anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
else:
    _anthropic_client = None


def _get_client_candidates() -> list[tuple]:
    """Return ordered (client, model_id, path_label) attempts.

    Bedrock first (primary), then the direct Anthropic API (fallback) when
    ANTHROPIC_API_KEY is set. Callers try each in order and drop to the
    demo/mock response if the list is empty or every attempt raises. A single
    tuple cannot express the "try Bedrock, on exception retry Anthropic" flow,
    so this returns the candidate list the callers iterate over.
    """
    candidates: list[tuple] = []
    if client is not None:
        candidates.append((client, BEDROCK_MODEL_ID, "bedrock"))
    if _anthropic_client is not None:
        candidates.append((_anthropic_client, ANTHROPIC_MODEL_ID, "anthropic"))
    return candidates

# Simple in-memory cache for market insights (60-second TTL)
_insights_cache = {}
_INSIGHTS_CACHE_TTL = 60  # seconds

# Graceful-degradation copy: shown when live AI is unreachable (missing/expired
# AWS credentials, network failure). Never 500 — see CLAUDE.md Architecture Notes.
_DEMO_FALLBACK: dict[Language, str] = {
    Language.EN: "Namaste! I'm Shreya. I'm in demo mode right now, so live AI responses are unavailable — but the risk profiler, goal planner, and dashboard all work fully. Please try again in a moment.",
    Language.HI: "नमस्ते! मैं श्रेया हूँ। अभी मैं demo mode में हूँ, इसलिए live AI उत्तर उपलब्ध नहीं हैं — लेकिन risk profiler, goal planner और dashboard पूरी तरह काम कर रहे हैं। कृपया थोड़ी देर में पुनः प्रयास करें।",
    Language.MR: "नमस्कार! मी श्रेया आहे. सध्या मी demo mode मध्ये आहे, त्यामुळे live AI उत्तरे उपलब्ध नाहीत — पण risk profiler, goal planner आणि dashboard पूर्णपणे काम करत आहेत. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
    Language.TA: "வணக்கம்! நான் ஷ்ரேயா. இப்போது நான் demo mode-ல் இருக்கிறேன், எனவே live AI பதில்கள் கிடைக்கவில்லை — ஆனால் risk profiler, goal planner மற்றும் dashboard முழுமையாக வேலை செய்கின்றன. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.",
    Language.BN: "নমস্কার! আমি শ্রেয়া। এখন আমি demo mode-এ আছি, তাই live AI উত্তর পাওয়া যাচ্ছে না — কিন্তু risk profiler, goal planner এবং dashboard সম্পূর্ণ কাজ করছে। অনুগ্রহ করে একটু পরে আবার চেষ্টা করুন।",
}

_STREAM_INTERRUPTED: dict[Language, str] = {
    Language.EN: "\n\n⚠️ The connection was interrupted — please try again.",
    Language.HI: "\n\n⚠️ कनेक्शन बाधित हो गया — कृपया पुनः प्रयास करें।",
    Language.MR: "\n\n⚠️ कनेक्शनमध्ये व्यत्यय आला — कृपया पुन्हा प्रयत्न करा.",
    Language.TA: "\n\n⚠️ இணைப்பு துண்டிக்கப்பட்டது — மீண்டும் முயற்சிக்கவும்.",
    Language.BN: "\n\n⚠️ সংযোগ বিঘ্নিত হয়েছে — আবার চেষ্টা করুন।",
}


async def stream_chat(
    message: str,
    history: list[ChatMessage],
    language: Language,
    context: str = "",
) -> AsyncIterator[str]:
    """Stream a Claude response for the wealth advisor chat."""
    candidates = _get_client_candidates()
    if not candidates:
        # Graceful fallback: demo-mode response if no live path is available
        logger.info("stream_chat path=demo (no client configured)")
        yield _DEMO_FALLBACK.get(language, _DEMO_FALLBACK[Language.EN])
        return

    system_prompt = get_system_prompt(language)
    if context:
        system_prompt += f"\n\n## Relevant IDBI Data Context\n{context}"

    # Trim history to MAX_HISTORY (keep only last N messages)
    trimmed_history = history[-MAX_HISTORY:] if len(history) > MAX_HISTORY else history
    messages = [{"role": m.role, "content": m.content} for m in trimmed_history]
    messages.append({"role": "user", "content": message})

    # Try Bedrock first, then the Anthropic direct API on failure.
    for api_client, model_id, path in candidates:
        streamed_any = False
        try:
            async with api_client.messages.stream(
                model=model_id,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                timeout=TIMEOUT_SECONDS,
            ) as stream:
                async for text in stream.text_stream:
                    streamed_any = True
                    yield text
            logger.info("stream_chat path=%s", path)
            return
        except Exception:
            if streamed_any:
                # Partial output already sent — retrying another provider would
                # duplicate text, so surface an interruption instead.
                logger.info("stream_chat path=%s interrupted mid-stream", path)
                yield _STREAM_INTERRUPTED.get(language, _STREAM_INTERRUPTED[Language.EN])
                return
            # Failed before any text streamed — try the next candidate.
            continue

    # Every live path failed before producing output — degrade, never die mid-demo.
    logger.info("stream_chat path=demo (all providers failed)")
    yield _DEMO_FALLBACK.get(language, _DEMO_FALLBACK[Language.EN])


# Structured fallback when live analysis is unavailable — matches the response schema
_PORTFOLIO_FALLBACK = {
    "summary": "Your portfolio shows a mix of equity and debt holdings — a detailed AI analysis is temporarily unavailable.",
    "recommendations": [
        "Review your equity/debt split against your risk profile",
        "Avoid letting large amounts sit idle in liquid funds",
        "Rebalance once a year to stay aligned with your goals",
    ],
    "sip_suggestion": "Consider a monthly SIP in a diversified equity fund category suited to your risk profile."
}


async def analyze_portfolio(portfolio_data: dict, language: Language) -> dict:
    """Analyze a portfolio and return structured recommendations as JSON."""
    if client is None:
        return dict(_PORTFOLIO_FALLBACK)

    system_prompt = get_system_prompt(language)
    
    # Add strict JSON output instruction
    json_instruction = """
    
IMPORTANT: You must respond with ONLY a valid JSON object. No markdown, no explanation, no additional text.
Your response must be exactly in this format:
{
    "summary": "One sentence overview of the portfolio",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
    "sip_suggestion": "Specific fund category and amount suggestion"
}

Respond in the language matching the user's input.
"""
    
    enhanced_prompt = f"""Analyze this portfolio and provide structured recommendations:

Portfolio Data:
{portfolio_data}

{json_instruction}"""

    try:
        response = await client.messages.create(
            model=BEDROCK_MODEL_ID,
            max_tokens=1024,
            system=system_prompt + json_instruction,
            messages=[{
                "role": "user",
                "content": enhanced_prompt
            }],
            timeout=TIMEOUT_SECONDS,
        )
    except Exception:
        # Bedrock unreachable (bad credentials, network) — degrade, never 500
        return dict(_PORTFOLIO_FALLBACK)

    response_text = response.content[0].text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()
    elif response_text.startswith("```"):
        response_text = response_text.replace("```", "").strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "summary": response_text[:200],
            "recommendations": ["Review portfolio allocation", "Consider diversification", "Rebalance periodically"],
            "sip_suggestion": "Consider starting with ₹5000/month in a balanced fund"
        }


async def generate_goal_plan(goals: list[dict], language: Language) -> str:
    """Generate a savings plan for the user's financial goals."""
    if client is None:
        return "I apologize, but I'm currently unable to generate your goal plan. Please ensure AWS credentials are properly configured."

    system_prompt = get_system_prompt(language)

    try:
        response = await client.messages.create(
            model=BEDROCK_MODEL_ID,
            max_tokens=2048,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Create a detailed savings and investment plan for these goals:\n\n{goals}"
            }],
            timeout=TIMEOUT_SECONDS,
        )
        return response.content[0].text
    except Exception:
        return "I'm unable to generate your goal plan right now. Please try again in a moment."


# Mock insights per language — used when live AI is unavailable
_MOCK_INSIGHTS: dict[Language, list[str]] = {
    Language.EN: [
        "Market volatility continues amid global economic uncertainty",
        "Banking sector shows resilience with NPA levels improving",
        "IT sector facing headwinds due to global slowdown concerns"
    ],
    Language.HI: [
        "वैश्विक आर्थिक अनिश्चितता के बीच बाजार की अस्थिरता जारी है",
        "एनपीए स्तर में सुधार के साथ बैंकिंग क्षेत्र मजबूत दिख रहा है",
        "वैश्विक मंदी की चिंताओं से आईटी क्षेत्र पर दबाव"
    ],
    Language.MR: [
        "वैश्विक आर्थिक अनिश्चितता आणि सर्व्हलेला बाजार अस्थिर",
        "बँक क्षेत्र एनपीए पातळीत सुधार करत आहे",
        "आयटी क्षेत्रावर ग्लोबल स्लोडाउनचा परिणाम"
    ],
    Language.TA: [
        "உலகளாவிய பொருளாதார நிச்சயமற்ற தன்மையின் போது சந்தை ஏற்ற இறக்கம் தொடர்கிறது",
        "என்பிஏ அளவுகள் மேம்படுவதால் வங்கி துறை எதிர்காலம் காண்கிறது",
        "உலகளாவிய மெதுவான செயல்பாடு காரணமாக ஐடி துறை அழுத்தம் எதிர்கொள்கிறது"
    ],
    Language.BN: [
        "বিশ্বব্যাপী অর্থনৈতিক অনিশ্চয়তার মধ্যে বাজারের অস্থিরতা অব্যাহত",
        "এনপিএ স্তরের উন্নতির সাথে ব্যাংকিং খাত স্থিতিস্থাপক দেখাচ্ছে",
        "বিশ্বব্যাপী মন্থরতার কারণে আইটি খাতের মন্থর গতি"
    ],
}


async def generate_market_insights(language: Language) -> list:
    """Generate daily personalized market insights as a JSON array of strings."""
    cache_key = f"insights_{language.value}"
    current_time = time.time()

    # Check cache
    if cache_key in _insights_cache:
        cached_data, cached_time = _insights_cache[cache_key]
        if current_time - cached_time < _INSIGHTS_CACHE_TTL:
            return cached_data

    candidates = _get_client_candidates()
    if not candidates:
        logger.info("generate_market_insights path=demo (no client configured)")
        return _MOCK_INSIGHTS.get(language, _MOCK_INSIGHTS[Language.EN])

    system_prompt = get_system_prompt(language)
    user_prompt = (
        f"Give me 3 brief market insights for Indian retail investors today. "
        f"Respond in {language.value}. Return as a JSON array of strings only, no markdown."
    )

    # Try Bedrock first, then the Anthropic direct API on failure.
    response = None
    for api_client, model_id, path in candidates:
        try:
            response = await api_client.messages.create(
                model=model_id,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=TIMEOUT_SECONDS,
            )
            logger.info("generate_market_insights path=%s", path)
            break
        except Exception:
            # Provider unreachable — try the next candidate.
            continue

    if response is None:
        # Every live path failed — serve mock insights, never 500.
        logger.info("generate_market_insights path=demo (all providers failed)")
        return _MOCK_INSIGHTS.get(language, _MOCK_INSIGHTS[Language.EN])

    response_text = response.content[0].text.strip()

    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()

        insights = json.loads(response_text)

        # Ensure it's a list
        if not isinstance(insights, list):
            insights = [insights]

        # Cache the result
        _insights_cache[cache_key] = (insights, current_time)
        return insights

    except (json.JSONDecodeError, TypeError):
        # Fallback if JSON parsing fails — wrap in array
        return [response_text]


async def generate_risk_explanation(profile: str, score: int, allocation: dict, language: Language) -> str:
    """Generate a personalized explanation for the risk profile."""
    fallback = f"Your risk profile is {profile} with a score of {score}. We recommend an allocation of {allocation}."
    if client is None:
        return fallback

    system_prompt = get_system_prompt(language)

    try:
        response = await client.messages.create(
            model=BEDROCK_MODEL_ID,
            max_tokens=256,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Explain in one sentence why a {profile} investor with score {score} should use this allocation: {allocation}"
            }],
            timeout=TIMEOUT_SECONDS,
        )
        return response.content[0].text
    except Exception:
        # Bedrock unreachable — quiz result must still render, never 500
        return fallback

