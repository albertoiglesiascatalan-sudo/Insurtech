"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("rss_url", sa.String(500)),
        sa.Column("source_type", sa.String(20), default="rss"),
        sa.Column("region", sa.String(50), default="global"),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("category", sa.String(100), default="general"),
        sa.Column("quality_score", sa.Float(), default=0.8),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("fetch_interval_minutes", sa.Integer(), default=30),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True)),
        sa.Column("description", sa.Text()),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(600), unique=True, nullable=False),
        sa.Column("url", sa.String(1000), unique=True, nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("content_raw", sa.Text()),
        sa.Column("summary_ai", sa.Text()),
        sa.Column("image_url", sa.String(1000)),
        sa.Column("author", sa.String(200)),
        sa.Column("topics", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("regions", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("reader_profiles", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("relevance_score", sa.Float(), default=0.5),
        sa.Column("embedding", Vector(1536)),
        sa.Column("is_duplicate", sa.Boolean(), default=False),
        sa.Column("duplicate_of", sa.Integer(), sa.ForeignKey("articles.id")),
        sa.Column("is_processed", sa.Boolean(), default=False),
        sa.Column("is_featured", sa.Boolean(), default=False),
        sa.Column("is_published", sa.Boolean(), default=True),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_index("ix_articles_is_duplicate", "articles", ["is_duplicate"])
    op.execute("CREATE INDEX ix_articles_topics ON articles USING gin(topics)")
    op.execute("CREATE INDEX ix_articles_regions ON articles USING gin(regions)")
    op.execute("CREATE INDEX ix_articles_profiles ON articles USING gin(reader_profiles)")
    op.execute(
        "CREATE INDEX ix_articles_fts ON articles USING gin(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(summary_ai,'')))"
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("hashed_password", sa.String(200)),
        sa.Column("reader_profile", sa.String(20), default="general"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_admin", sa.Boolean(), default=False),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("verification_token", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("topics", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("regions", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("reader_profiles", sa.ARRAY(sa.String()), server_default="{}"),
        sa.Column("frequency", sa.String(20), default="weekly"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("unsubscribe_token", sa.String(200)),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_sent_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "newsletters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=False),
        sa.Column("reader_profile", sa.String(20), nullable=False),
        sa.Column("edition_type", sa.String(20), nullable=False),
        sa.Column("edition_number", sa.Integer(), default=1),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "newsletter_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("newsletter_id", sa.Integer(), sa.ForeignKey("newsletters.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resend_id", sa.String(200)),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("clicked_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "article_id"),
    )


def downgrade() -> None:
    op.drop_table("bookmarks")
    op.drop_table("newsletter_logs")
    op.drop_table("newsletters")
    op.drop_table("subscriptions")
    op.drop_table("users")
    op.drop_table("articles")
    op.drop_table("sources")
