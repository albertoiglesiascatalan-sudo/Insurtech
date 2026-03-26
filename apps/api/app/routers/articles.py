from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.article import Article
from app.models.source import Source
from app.schemas.article import ArticleOut, ArticleList

router = APIRouter(prefix="/articles", tags=["articles"])

TOPICS = [
    "embedded-insurance", "health-tech", "auto-insurance", "pc-innovation",
    "climate-parametric", "regulatory-policy", "funding-ma", "partnerships",
    "product-launches", "ai-insurance", "cyber-insurance", "life-insurance",
    "distribution", "claims-tech", "underwriting-tech",
]

REGIONS = ["US", "EU", "APAC", "LATAM", "MEA", "global"]
PROFILES = ["investor", "founder", "general"]


def _build_query(
    topic: str | None,
    region: str | None,
    profile: str | None,
    source_slug: str | None,
    sentiment: str | None,
    search: str | None,
    featured_only: bool,
):
    q = (
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.is_published == True, Article.is_duplicate == False)  # noqa: E712
    )
    if topic:
        q = q.where(Article.topics.contains([topic]))
    if region:
        q = q.where(Article.regions.contains([region]))
    if profile:
        q = q.where(Article.reader_profiles.contains([profile]))
    if sentiment:
        q = q.where(Article.sentiment == sentiment)
    if featured_only:
        q = q.where(Article.is_featured == True)  # noqa: E712
    if source_slug:
        q = q.join(Source).where(Source.slug == source_slug)
    if search:
        q = q.where(
            or_(
                Article.title.ilike(f"%{search}%"),
                Article.summary_ai.ilike(f"%{search}%"),
            )
        )
    return q


@router.get("", response_model=ArticleList)
async def list_articles(
    topic: str | None = None,
    region: str | None = None,
    profile: str | None = None,
    source_slug: str | None = None,
    sentiment: str | None = None,
    search: str | None = None,
    featured_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    base_q = _build_query(topic, region, profile, source_slug, sentiment, search, featured_only)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    items_q = (
        base_q
        .order_by(Article.published_at.desc().nullslast(), Article.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(items_q)).scalars().all()

    return ArticleList(
        items=[ArticleOut.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/topics", response_model=list[dict])
async def list_topics():
    topic_labels = {
        "embedded-insurance": "Embedded Insurance",
        "health-tech": "Health InsurTech",
        "auto-insurance": "Auto Insurance Tech",
        "pc-innovation": "P&C Innovation",
        "climate-parametric": "Climate & Parametric",
        "regulatory-policy": "Regulatory & Policy",
        "funding-ma": "Funding & M&A",
        "partnerships": "Partnerships",
        "product-launches": "Product Launches",
        "ai-insurance": "AI in Insurance",
        "cyber-insurance": "Cyber Insurance",
        "life-insurance": "Life Insurance Tech",
        "distribution": "Distribution",
        "claims-tech": "Claims Tech",
        "underwriting-tech": "Underwriting Tech",
    }
    return [{"slug": k, "label": v} for k, v in topic_labels.items()]


@router.get("/regions", response_model=list[dict])
async def list_regions():
    return [
        {"slug": "US", "label": "United States"},
        {"slug": "EU", "label": "Europe"},
        {"slug": "APAC", "label": "Asia Pacific"},
        {"slug": "LATAM", "label": "Latin America"},
        {"slug": "MEA", "label": "Middle East & Africa"},
        {"slug": "global", "label": "Global"},
    ]


@router.get("/{slug}", response_model=ArticleOut)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.slug == slug, Article.is_published == True)  # noqa: E712
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleOut.model_validate(article)
