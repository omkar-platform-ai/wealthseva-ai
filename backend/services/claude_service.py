"""
Claude API service — handles all LLM calls, streaming, and tool use.
"""
import os
from typing import AsyncIterator
import anthropic
from models.schemas import Language, ChatMessage
from services.language_service import get_system_prompt

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


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
