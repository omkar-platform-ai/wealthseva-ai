"""
Claude API service — handles all LLM calls, streaming, and tool use.
Uses Amazon Bedrock for model inference with IAM authentication.
"""
import os
import json
import time
from typing import AsyncIterator
import anthropic
from models.schemas import Language, ChatMessage
from services.language_service import get_system_prompt

# Bedrock configuration
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-south-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
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

if _aws_credentials_available:
    client = anthropic.AsyncAnthropicBedrock(
        region=BEDROCK_REGION,
    )
else:
    client = None

# Simple in-memory cache for market insights (60-second TTL)
_insights_cache = {}
_INSIGHTS_CACHE_TTL = 60  # seconds


async def stream_chat(
    message: str,
    history: list[ChatMessage],
    language: Language,
    context: str = "",
) -> AsyncIterator[str]:
    """Stream a Claude response for the wealth advisor chat."""
    if client is None:
        # Graceful fallback: return mock response if AWS credentials not configured
        yield "Mock response — add ANTHROPIC_API_KEY to .env"
        return

    system_prompt = get_system_prompt(language)
    if context:
        system_prompt += f"\n\n## Relevant IDBI Data Context\n{context}"

    # Trim history to MAX_HISTORY (keep only last N messages)
    trimmed_history = history[-MAX_HISTORY:] if len(history) > MAX_HISTORY else history
    messages = [{"role": m.role, "content": m.content} for m in trimmed_history]
    messages.append({"role": "user", "content": message})

    async with client.messages.stream(
        model=BEDROCK_MODEL_ID,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        timeout=TIMEOUT_SECONDS,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def analyze_portfolio(portfolio_data: dict, language: Language) -> dict:
    """Analyze a portfolio and return structured recommendations as JSON."""
    if client is None:
        return {
            "summary": "Service temporarily unavailable. Please ensure AWS credentials are properly configured.",
            "recommendations": ["Check AWS credentials", "Verify Bedrock access", "Contact support"],
            "sip_suggestion": "N/A - Service unavailable"
        }

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

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=1024,
        system=system_prompt + json_instruction,
        messages=[{
            "role": "user",
            "content": enhanced_prompt
        }],
    )
    
    import json
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

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=2048,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Create a detailed savings and investment plan for these goals:\n\n{goals}"
        }],
    )
    return response.content[0].text


async def generate_market_insights(language: Language) -> list:
    """Generate daily personalized market insights as a JSON array of strings."""
    cache_key = f"insights_{language.value}"
    current_time = time.time()

    # Check cache
    if cache_key in _insights_cache:
        cached_data, cached_time = _insights_cache[cache_key]
        if current_time - cached_time < _INSIGHTS_CACHE_TTL:
            return cached_data

    if client is None:
        # Return mock insights in the requested language
        mock_insights = {
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
        return mock_insights.get(language, mock_insights[Language.EN])

    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Give me 3 brief market insights for Indian retail investors today. Respond in {language.value}. Return as a JSON array of strings only, no markdown."
        }],
        timeout=TIMEOUT_SECONDS,
    )

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
    if client is None:
        return f"Your risk profile is {profile} with a score of {score}. We recommend an allocation of {allocation}."

    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=256,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Explain in one sentence why a {profile} investor with score {score} should use this allocation: {allocation}"
        }],
    )
    return response.content[0].text

