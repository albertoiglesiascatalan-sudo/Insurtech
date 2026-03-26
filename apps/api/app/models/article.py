from datetime import datetime
from sqlalchemy import String, Boolean, Float, Integer, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(600), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)

    # Content
    content_raw: Mapped[str | None] = mapped_column(Text)
    summary_ai: Mapped[str | None] = mapped_column(Text)  # AI-generated 2-3 sentence summary
    image_url: Mapped[str | None] = mapped_column(String(1000))
    author: Mapped[str | None] = mapped_column(String(200))

    # AI-enriched metadata
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    regions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    reader_profiles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    sentiment: Mapped[str | None] = mapped_column(String(20))  # positive | neutral | negative
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5)

    # Deduplication
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))

    # Status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relations
    source: Mapped["Source"] = relationship("Source", back_populates="articles")  # noqa: F821
    bookmarks: Mapped[list["Bookmark"]] = relationship("Bookmark", back_populates="article")  # noqa: F821
