from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.article import Article
from app.schemas.article import ArticleOut, ArticleList

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=ArticleList)
async def search_articles(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search using PostgreSQL tsvector."""
    offset = (page - 1) * page_size

    count_stmt = text(
        """
        SELECT COUNT(*) FROM articles
        WHERE is_published = true AND is_duplicate = false
        AND to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary_ai,''))
            @@ plainto_tsquery('english', :q)
        """
    )
    total = (await db.execute(count_stmt, {"q": q})).scalar_one()

    stmt = text(
        """
        SELECT id FROM articles
        WHERE is_published = true AND is_duplicate = false
        AND to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary_ai,''))
            @@ plainto_tsquery('english', :q)
        ORDER BY
            ts_rank(
                to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary_ai,'')),
                plainto_tsquery('english', :q)
            ) DESC,
            published_at DESC NULLS LAST
        LIMIT :limit OFFSET :offset
        """
    )
    rows = (await db.execute(stmt, {"q": q, "limit": page_size, "offset": offset})).fetchall()
    ids = [r[0] for r in rows]

    if not ids:
        return ArticleList(items=[], total=0, page=page, page_size=page_size, has_next=False)

    articles_q = (
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.id.in_(ids))
    )
    articles_map = {a.id: a for a in (await db.execute(articles_q)).scalars().all()}
    items = [ArticleOut.model_validate(articles_map[i]) for i in ids if i in articles_map]

    return ArticleList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )
