from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.source import Source
from app.schemas.source import SourceOut, SourceCreate, SourceUpdate
from app.auth import require_admin
from slugify import slugify

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    q = select(Source)
    if active_only:
        q = q.where(Source.is_active == True)  # noqa: E712
    q = q.order_by(Source.quality_score.desc(), Source.name)
    result = await db.execute(q)
    return [SourceOut.model_validate(s) for s in result.scalars().all()]


@router.get("/{slug}", response_model=SourceOut)
async def get_source(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.slug == slug))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceOut.model_validate(source)


@router.post("", response_model=SourceOut)
async def create_source(
    data: SourceCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    slug = slugify(data.name)
    source = Source(slug=slug, **data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceOut.model_validate(source)


@router.patch("/{slug}", response_model=SourceOut)
async def update_source(
    slug: str,
    data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(select(Source).where(Source.slug == slug))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    await db.commit()
    await db.refresh(source)
    return SourceOut.model_validate(source)
