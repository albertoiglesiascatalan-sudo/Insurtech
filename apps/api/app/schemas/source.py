from datetime import datetime
from pydantic import BaseModel


class SourceOut(BaseModel):
    id: int
    name: str
    slug: str
    url: str
    rss_url: str | None = None
    source_type: str
    region: str
    language: str
    category: str
    quality_score: float
    is_active: bool
    description: str | None = None
    logo_url: str | None = None
    last_fetched_at: datetime | None = None

    model_config = {"from_attributes": True}


class SourceCreate(BaseModel):
    name: str
    url: str
    rss_url: str | None = None
    source_type: str = "rss"
    region: str = "global"
    language: str = "en"
    category: str = "general"
    description: str | None = None
    logo_url: str | None = None
    fetch_interval_minutes: int = 30


class SourceUpdate(BaseModel):
    name: str | None = None
    rss_url: str | None = None
    is_active: bool | None = None
    quality_score: float | None = None
    fetch_interval_minutes: int | None = None
