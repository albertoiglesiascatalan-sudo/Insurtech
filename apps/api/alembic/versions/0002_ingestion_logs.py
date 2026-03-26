"""Add ingestion_logs table

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("articles_found", sa.Integer(), default=0),
        sa.Column("articles_new", sa.Integer(), default=0),
        sa.Column("articles_dup", sa.Integer(), default=0),
        sa.Column("status", sa.String(20)),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_ingestion_logs_started_at", "ingestion_logs", ["started_at"])
    op.create_index("ix_ingestion_logs_source_id", "ingestion_logs", ["source_id"])


def downgrade() -> None:
    op.drop_table("ingestion_logs")
