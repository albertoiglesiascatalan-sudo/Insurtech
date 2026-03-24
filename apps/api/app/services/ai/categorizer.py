"""AI-powered article categorization: topics, regions, reader profiles, sentiment."""
import json
import logging
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TOPICS = [
    "embedded-insurance", "health-tech", "auto-insurance", "pc-innovation",
    "climate-parametric", "regulatory-policy", "funding-ma", "partnerships",
    "product-launches", "ai-insurance", "cyber-insurance", "life-insurance",
    "distribution", "claims-tech", "underwriting-tech",
]

REGIONS = ["US", "EU", "APAC", "LATAM", "MEA", "global"]

SYSTEM_PROMPT = f"""You are an insurtech content classifier. Given an article title and summary,
classify it and return a JSON object with these exact fields:
- topics: array of 1-3 topics from: {TOPICS}
- regions: array of 1-3 regions from: {REGIONS}
- reader_profiles: array of profiles this is most relevant to: ["investor", "founder", "general"]
  - investor: funding rounds, M&A, valuations, market data, growth metrics
  - founder: product launches, partnerships, regulatory, technology, go-to-market
  - general: consumer impact, macro trends, innovation, broad industry news
- sentiment: one of "positive", "neutral", "negative"
- relevance_score: float 0.0-1.0 indicating how relevant this is to insurtech specifically

Return ONLY valid JSON, no markdown, no explanation."""


async def categorize(title: str, content: str) -> dict | None:
    """Categorize an article into topics, regions, profiles, sentiment."""
    if not settings.openai_api_key:
        return _fallback_categorization()
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model_categorize,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nContent: {content[:1500]}",
                },
            ],
            max_tokens=200,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        # Validate and sanitize
        return {
            "topics": [t for t in result.get("topics", []) if t in TOPICS][:3],
            "regions": [r for r in result.get("regions", []) if r in REGIONS][:3],
            "reader_profiles": [
                p for p in result.get("reader_profiles", ["general"])
                if p in ("investor", "founder", "general")
            ],
            "sentiment": result.get("sentiment", "neutral"),
            "relevance_score": float(result.get("relevance_score", 0.7)),
        }
    except Exception as e:
        logger.warning(f"Categorization failed: {e}")
        return _fallback_categorization()


def _fallback_categorization() -> dict:
    return {
        "topics": [],
        "regions": ["global"],
        "reader_profiles": ["general"],
        "sentiment": "neutral",
        "relevance_score": 0.5,
    }
