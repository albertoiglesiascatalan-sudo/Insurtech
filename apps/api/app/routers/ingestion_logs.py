from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db
from app.auth import require_admin

router = APIRouter(prefix="/admin/ingestion-logs", tags=["admin"])


@router.get("")
async def list_ingestion_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List recent ingestion logs (no auth required for now — add require_admin in prod)."""
    try:
        stmt = text(
            """
            SELECT
                il.id, il.started_at, il.completed_at,
                il.articles_found, il.articles_new, il.articles_dup,
                il.status, il.error_message,
                s.name as source_name
            FROM ingestion_logs il
            LEFT JOIN sources s ON s.id = il.source_id
            ORDER BY il.started_at DESC
            LIMIT :limit
            """
        )
        result = await db.execute(stmt, {"limit": limit})
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "started_at": r[1].isoformat() if r[1] else None,
                "completed_at": r[2].isoformat() if r[2] else None,
                "articles_found": r[3],
                "articles_new": r[4],
                "articles_dup": r[5],
                "status": r[6],
                "error_message": r[7],
                "source_name": r[8],
            }
            for r in rows
        ]
    except Exception:
        return []
