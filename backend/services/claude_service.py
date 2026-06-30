"""
Claude API service — handles all LLM calls, streaming, and tool use.
Uses Amazon Bedrock for model inference with IAM authentication.
"""
import os
from typing import AsyncIterator
import anthropic
from models.schemas import Language, ChatMessage
from services.language_service import get_system_prompt

# Bedrock configuration
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-south-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")

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


async def stream_chat(
    message: str,
    history: list[ChatMessage],
    language: Language,
    context: str = "",
) -> AsyncIterator[str]:
    """Stream a Claude response for the wealth advisor chat."""
    if client is None:
        # Graceful fallback: return mock response if AWS credentials not configured
        yield "I apologize, but I'm currently unable to connect to my AI backend. Please ensure AWS credentials are properly configured."
        return

    system_prompt = get_system_prompt(language)
    if context:
        system_prompt += f"\n\n## Relevant IDBI Data Context\n{context}"

    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": message})

    async with client.messages.stream(
        model=BEDROCK_MODEL_ID,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def analyze_portfolio(portfolio_data: dict, language: Language) -> str:
    """Analyze a portfolio and return structured recommendations."""
    if client is None:
        return "I apologize, but I'm currently unable to analyze your portfolio. Please ensure AWS credentials are properly configured."

    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=2048,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Analyze this portfolio and give me personalized recommendations:\n\n{portfolio_data}"
        }],
    )
    return response.content[0].text


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


async def generate_market_insights(language: Language) -> str:
    """Generate daily personalized market insights."""
    if client is None:
        return "I apologize, but I'm currently unable to generate market insights. Please ensure AWS credentials are properly configured."

    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=BEDROCK_MODEL_ID,
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": "Give me today's key market insights relevant to Indian retail investors in 3-4 concise points."
        }],
    )
    return response.content[0].text



async def stream_chat(
    message: str,
    history: list[ChatMessage],
    language: Language,
    context: str = "",
) -> AsyncIterator[str]:
    """Stream a Claude response for the wealth advisor chat."""
    system_prompt = get_system_prompt(language)
    if context:
        system_prompt += f"\n\n## Relevant IDBI Data Context\n{context}"

    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": message})

    async with client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def analyze_portfolio(portfolio_data: dict, language: Language) -> str:
    """Analyze a portfolio and return structured recommendations."""
    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Analyze this portfolio and give me personalized recommendations:\n\n{portfolio_data}"
        }],
    )
    return response.content[0].text


async def generate_goal_plan(goals: list[dict], language: Language) -> str:
    """Generate a savings plan for the user's financial goals."""
    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Create a detailed savings and investment plan for these goals:\n\n{goals}"
        }],
    )
    return response.content[0].text


async def generate_market_insights(language: Language) -> str:
    """Generate daily personalized market insights."""
    system_prompt = get_system_prompt(language)

    response = await client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": "Give me today's key market insights relevant to Indian retail investors in 3-4 concise points."
        }],
    )
    return response.content[0].text
