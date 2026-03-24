"""
News Verifier — AI-powered credibility and fact-checking service.

Checks:
1. Source credibility score
2. Cross-reference with other articles on same topic (pgvector)
3. Claim consistency analysis (GPT-4o)
4. Red flags: sensationalist language, missing attribution, unverified claims
5. Overall credibility verdict
"""
import json
import logging
from dataclasses import dataclass
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.config import get_settings
from app.models.article import Article
from app.models.source import Source

logger = logging.getLogger(__name__)
settings = get_settings()

VERIFIER_PROMPT = """You are a professional fact-checker and media analyst specializing in insurtech and financial news.

Analyze the following article and return a JSON object with this exact structure:
{
  "credibility_score": <float 0.0-1.0>,
  "verdict": "<one of: verified|likely_true|unverified|misleading|false>",
  "verdict_label": "<short human-readable label, max 30 chars>",
  "confidence": <float 0.0-1.0>,
  "summary": "<2-3 sentence analysis of credibility>",
  "red_flags": [<list of strings, each a specific concern, empty if none>],
  "positive_signals": [<list of strings, each a positive credibility signal>],
  "claim_analysis": [
    {
      "claim": "<specific claim from the article>",
      "assessment": "<verified|plausible|unverified|questionable>",
      "note": "<brief explanation>"
    }
  ],
  "recommendation": "<one of: trustworthy|read_with_caution|verify_independently|discard>"
}

Credibility signals to check:
- Named sources and quotes (good) vs anonymous sources (bad)
- Specific data, numbers, dates (good) vs vague claims (bad)
- Links to official announcements, filings, press releases (good)
- Sensationalist or clickbait language (bad)
- Consistent with known industry facts (good)
- Extraordinary claims without evidence (bad)
- Source reputation and track record
- Whether claims are independently verifiable

Return ONLY valid JSON, no markdown."""


@dataclass
class VerificationResult:
    article_id: int
    title: str
    source_name: str
    source_quality: float
    credibility_score: float
    verdict: str
    verdict_label: str
    confidence: float
    summary: str
    red_flags: list[str]
    positive_signals: list[str]
    claim_analysis: list[dict]
    recommendation: str
    corroborating_articles: list[dict]
    contradicting_articles: list[dict]


async def verify_article(db: AsyncSession, article_id: int) -> VerificationResult | None:
    """Run full verification pipeline on an article."""
    # 1. Fetch article + source
    result = await db.execute(
        select(Article, Source)
        .join(Source, Source.id == Article.source_id)
        .where(Article.id == article_id)
    )
    row = result.first()
    if not row:
        return None

    article, source = row

    # 2. Find corroborating/contradicting articles via pgvector
    corroborating = []
    contradicting = []
    if article.embedding:
        similar = await _find_similar_articles(db, article)
        corroborating = [a for a in similar if a["sentiment"] == article.sentiment][:3]
        contradicting = [a for a in similar if a["sentiment"] != article.sentiment and article.sentiment][:2]

    # 3. AI credibility analysis
    ai_result = await _ai_verify(article, source)

    # 4. Merge source quality into credibility score
    source_factor = source.quality_score * 0.3
    ai_score = ai_result.get("credibility_score", 0.5) * 0.7
    final_score = min(1.0, source_factor + ai_score)

    return VerificationResult(
        article_id=article.id,
        title=article.title,
        source_name=source.name,
        source_quality=source.quality_score,
        credibility_score=round(final_score, 2),
        verdict=ai_result.get("verdict", "unverified"),
        verdict_label=ai_result.get("verdict_label", "Unverified"),
        confidence=ai_result.get("confidence", 0.5),
        summary=ai_result.get("summary", ""),
        red_flags=ai_result.get("red_flags", []),
        positive_signals=ai_result.get("positive_signals", []),
        claim_analysis=ai_result.get("claim_analysis", []),
        recommendation=ai_result.get("recommendation", "read_with_caution"),
        corroborating_articles=corroborating,
        contradicting_articles=contradicting,
    )


async def _find_similar_articles(db: AsyncSession, article: Article) -> list[dict]:
    """Find articles on the same story using pgvector similarity."""
    try:
        stmt = text(
            """
            SELECT a.id, a.title, a.url, a.sentiment, a.summary_ai, s.name as source_name,
                   1 - (a.embedding <=> :emb::vector) as similarity
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            WHERE a.id != :article_id
              AND a.embedding IS NOT NULL
              AND a.is_published = true
              AND 1 - (a.embedding <=> :emb::vector) > 0.75
            ORDER BY a.embedding <=> :emb::vector
            LIMIT 8
            """
        )
        result = await db.execute(
            stmt,
            {"emb": str(article.embedding), "article_id": article.id}
        )
        rows = result.fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "url": r[2],
                "sentiment": r[3],
                "summary": r[4],
                "source": r[5],
                "similarity": round(float(r[6]), 2),
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning(f"Similar article search failed: {e}")
        return []


async def _ai_verify(article: Article, source: Source) -> dict:
    """Run GPT-4o credibility analysis on the article."""
    if not settings.openai_api_key:
        return _fallback_verification(source)

    content = f"""
Source: {source.name} (quality score: {source.quality_score:.0%}, category: {source.category})
Region: {source.region}
Title: {article.title}
Published: {article.published_at}
Author: {article.author or 'Not specified'}

Content:
{(article.content_raw or article.summary_ai or '')[:3000]}
"""

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o",  # Use full GPT-4o for verification — accuracy matters
            messages=[
                {"role": "system", "content": VERIFIER_PROMPT},
                {"role": "user", "content": content},
            ],
            max_tokens=800,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"AI verification failed: {e}")
        return _fallback_verification(source)


def _fallback_verification(source: Source) -> dict:
    score = source.quality_score
    if score >= 0.9:
        verdict, label, rec = "likely_true", "High credibility source", "trustworthy"
    elif score >= 0.7:
        verdict, label, rec = "unverified", "Standard source", "read_with_caution"
    else:
        verdict, label, rec = "unverified", "Unknown credibility", "verify_independently"

    return {
        "credibility_score": score,
        "verdict": verdict,
        "verdict_label": label,
        "confidence": 0.4,
        "summary": f"Verification based on source quality score ({score:.0%}). Full AI analysis unavailable.",
        "red_flags": [],
        "positive_signals": [f"Published by {source.name}"],
        "claim_analysis": [],
        "recommendation": rec,
    }
