"""Semantic deduplication using pgvector cosine similarity."""
import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def compute_embedding(text_content: str) -> list[float] | None:
    """Generate text-embedding-3-small vector for a piece of text."""
    if not settings.openai_api_key or not text_content.strip():
        return None
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text_content[:8000],
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None


async def is_duplicate(
    db: AsyncSession,
    embedding: list[float],
    source_id: int,
) -> int | None:
    """
    Check if an article with similar embedding exists.
    Returns the ID of the duplicate article if found, else None.
    """
    threshold = settings.deduplication_threshold
    try:
        # pgvector cosine distance: 1 - cosine_similarity
        # distance < (1 - threshold) means similarity > threshold
        stmt = text(
            """
            SELECT id FROM articles
            WHERE embedding IS NOT NULL
            AND is_duplicate = false
            AND (embedding <=> :emb::vector) < :dist
            ORDER BY embedding <=> :emb::vector
            LIMIT 1
            """
        )
        result = await db.execute(stmt, {"emb": str(embedding), "dist": 1 - threshold})
        row = result.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.warning(f"Deduplication check failed: {e}")
        return None
