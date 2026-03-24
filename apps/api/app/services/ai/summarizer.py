"""AI-powered article summarization."""
import logging
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are an expert insurtech journalist. Given an article title and content,
write a concise 2-3 sentence summary that captures the key insight, the companies involved,
and why it matters for the insurtech industry. Be factual, precise, and use professional tone.
Never add opinions or speculation. Output only the summary text, no preamble."""


async def summarize(title: str, content: str) -> str | None:
    """Generate a 2-3 sentence AI summary of an article."""
    if not settings.openai_api_key:
        return None
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model_summarize,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nContent: {content[:3000]}",
                },
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Summarization failed: {e}")
        return None
