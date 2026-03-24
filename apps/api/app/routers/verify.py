from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.ai.verifier import verify_article, VerificationResult
from pydantic import BaseModel

router = APIRouter(prefix="/verify", tags=["verification"])


class VerificationOut(BaseModel):
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


@router.get("/{article_id}", response_model=VerificationOut)
async def verify(article_id: int, db: AsyncSession = Depends(get_db)):
    """
    Run AI-powered credibility verification on an article.
    Checks source quality, claim analysis, and cross-references with similar articles.
    """
    result = await verify_article(db, article_id)
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    return VerificationOut(**result.__dict__)
