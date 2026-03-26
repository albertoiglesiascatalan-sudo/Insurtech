from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.article import Article
from app.models.source import Source
from app.models.user import User
from app.models.subscription import Subscription
from app.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    articles_count = (await db.execute(select(func.count()).select_from(Article))).scalar_one()
    sources_count = (await db.execute(select(func.count()).select_from(Source).where(Source.is_active == True))).scalar_one()  # noqa: E712
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    subs_count = (await db.execute(select(func.count()).select_from(Subscription).where(Subscription.is_active == True))).scalar_one()  # noqa: E712
    duplicates_count = (await db.execute(select(func.count()).select_from(Article).where(Article.is_duplicate == True))).scalar_one()  # noqa: E712

    return {
        "articles_total": articles_count,
        "articles_duplicates": duplicates_count,
        "sources_active": sources_count,
        "users_total": users_count,
        "subscribers_active": subs_count,
    }


@router.post("/ingest")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    _=Depends(require_admin),
):
    """Manually trigger feed ingestion."""
    from app.services.ingestion.scheduler import run_ingestion_now
    background_tasks.add_task(run_ingestion_now)
    return {"message": "Ingestion triggered in background"}


@router.post("/articles/{article_id}/feature")
async def toggle_feature(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    article.is_featured = not article.is_featured
    await db.commit()
    return {"is_featured": article.is_featured}


@router.post("/articles/{article_id}/unpublish")
async def unpublish_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    article.is_published = False
    await db.commit()
    return {"message": "Unpublished"}


@router.post("/newsletter/send")
async def send_newsletter(
    profile: str,
    frequency: str,
    background_tasks: BackgroundTasks,
    _=Depends(require_admin),
):
    from app.services.email.sender import send_newsletter_batch
    background_tasks.add_task(send_newsletter_batch, profile=profile, frequency=frequency)
    return {"message": f"Newsletter {frequency}/{profile} queued for sending"}
