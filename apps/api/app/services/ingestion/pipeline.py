"""Ingestion pipeline: fetch → deduplicate → AI enrich → save."""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.article import Article
from app.models.source import Source
from app.services.ingestion.feed_fetcher import fetch_feed, RawArticle
from app.services.ai.deduplicator import is_duplicate, compute_embedding
from app.services.ai.summarizer import summarize
from app.services.ai.categorizer import categorize
from slugify import slugify

logger = logging.getLogger(__name__)


async def _save_article(db: AsyncSession, raw: RawArticle) -> Article | None:
    """Save a raw article to DB, running full AI pipeline."""
    # Check URL uniqueness
    existing = await db.execute(select(Article).where(Article.url == raw["url"]))
    if existing.scalar_one_or_none():
        return None  # Already ingested

    # Generate slug
    slug_base = slugify(raw["title"])[:550]
    slug = slug_base
    counter = 1
    while (await db.execute(select(Article).where(Article.slug == slug))).scalar_one_or_none():
        slug = f"{slug_base}-{counter}"
        counter += 1

    # Compute embedding for deduplication
    text_for_embedding = f"{raw['title']} {raw.get('content_raw', '') or ''}"[:2000]
    embedding = await compute_embedding(text_for_embedding)

    # Check semantic deduplication
    dup_id = None
    if embedding:
        dup_id = await is_duplicate(db, embedding, raw["source_id"])

    # AI summarization
    summary = None
    if raw.get("content_raw") and not dup_id:
        summary = await summarize(raw["title"], raw.get("content_raw", "") or "")

    # AI categorization
    cats = None
    if not dup_id:
        cats = await categorize(raw["title"], summary or raw.get("content_raw", "") or "")

    article = Article(
        title=raw["title"],
        slug=slug,
        url=raw["url"],
        source_id=raw["source_id"],
        content_raw=raw.get("content_raw"),
        summary_ai=summary,
        image_url=raw.get("image_url"),
        author=raw.get("author"),
        published_at=raw.get("published_at"),
        embedding=embedding,
        is_duplicate=dup_id is not None,
        duplicate_of=dup_id,
        is_processed=True,
        topics=cats.get("topics", []) if cats else [],
        regions=cats.get("regions", []) if cats else [],
        reader_profiles=cats.get("reader_profiles", []) if cats else [],
        sentiment=cats.get("sentiment") if cats else None,
        relevance_score=cats.get("relevance_score", 0.5) if cats else 0.5,
    )
    db.add(article)
    return article


async def ingest_source(source: Source) -> int:
    """Fetch and process all articles from a single source. Returns count saved."""
    saved = 0
    try:
        if source.source_type == "rss" and source.rss_url:
            raw_articles = await fetch_feed(source.rss_url, source.id)
        else:
            logger.info(f"Skipping scrape-only source {source.name} (not yet configured)")
            return 0

        async with AsyncSessionLocal() as db:
            tasks = [_save_article(db, raw) for raw in raw_articles]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.error(f"Error saving article: {r}")
                elif r is not None:
                    saved += 1
            await db.commit()

            # Update last_fetched_at
            source_db = await db.get(Source, source.id)
            if source_db:
                source_db.last_fetched_at = datetime.now(timezone.utc)
                await db.commit()

    except Exception as e:
        logger.error(f"Failed to ingest source {source.name}: {e}")

    logger.info(f"Ingested {saved} new articles from {source.name}")
    return saved


async def run_all_sources() -> dict:
    """Run ingestion for all active sources."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Source).where(Source.is_active == True))  # noqa: E712
        sources = result.scalars().all()

    logger.info(f"Starting ingestion for {len(sources)} sources")
    totals = await asyncio.gather(*[ingest_source(s) for s in sources])
    total_saved = sum(totals)
    logger.info(f"Ingestion complete: {total_saved} new articles saved")
    return {"sources_processed": len(sources), "articles_saved": total_saved}
