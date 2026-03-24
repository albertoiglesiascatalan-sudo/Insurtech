from datetime import datetime
from pydantic import BaseModel


class SourceRef(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None = None
    region: str

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    url: str
    summary_ai: str | None = None
    image_url: str | None = None
    author: str | None = None
    topics: list[str]
    regions: list[str]
    reader_profiles: list[str]
    sentiment: str | None = None
    relevance_score: float
    is_featured: bool
    published_at: datetime | None = None
    scraped_at: datetime
    source: SourceRef

    model_config = {"from_attributes": True}


class ArticleList(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    page_size: int
    has_next: bool


class ArticleFilter(BaseModel):
    topic: str | None = None
    region: str | None = None
    profile: str | None = None
    source_slug: str | None = None
    sentiment: str | None = None
    search: str | None = None
    featured_only: bool = False
    page: int = 1
    page_size: int = 20
