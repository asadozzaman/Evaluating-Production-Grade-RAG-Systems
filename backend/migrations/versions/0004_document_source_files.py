"""add document source file metadata

Revision ID: 0004_doc_sources
Revises: 0003_chunk_source_cascade
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_doc_sources"
down_revision: Union[str, None] = "0003_chunk_source_cascade"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "source_documents",
        sa.Column("source_kind", sa.String(length=20), server_default="uri", nullable=False),
    )
    op.add_column("source_documents", sa.Column("original_file_name", sa.String(length=255), nullable=True))
    op.add_column("source_documents", sa.Column("stored_file_name", sa.String(length=255), nullable=True))
    op.add_column("source_documents", sa.Column("content_type", sa.String(length=100), nullable=True))
    op.add_column("source_documents", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("source_documents", sa.Column("storage_path", sa.String(length=500), nullable=True))

    op.execute(
        "UPDATE source_documents "
        "SET source_uri = 'legacy://source-document/' || id "
        "WHERE source_kind = 'uri' AND source_uri IS NULL"
    )

    op.create_check_constraint(
        "ck_source_documents_source_kind",
        "source_documents",
        "source_kind IN ('uri', 'file')",
    )
    op.create_check_constraint(
        "ck_source_documents_uri_requires_source_uri",
        "source_documents",
        "source_kind <> 'uri' OR source_uri IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_source_documents_file_requires_storage_path",
        "source_documents",
        "source_kind <> 'file' OR storage_path IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_source_documents_file_size_non_negative",
        "source_documents",
        "file_size_bytes IS NULL OR file_size_bytes >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_source_documents_file_size_non_negative", "source_documents", type_="check")
    op.drop_constraint("ck_source_documents_file_requires_storage_path", "source_documents", type_="check")
    op.drop_constraint("ck_source_documents_uri_requires_source_uri", "source_documents", type_="check")
    op.drop_constraint("ck_source_documents_source_kind", "source_documents", type_="check")
    op.drop_column("source_documents", "storage_path")
    op.drop_column("source_documents", "file_size_bytes")
    op.drop_column("source_documents", "content_type")
    op.drop_column("source_documents", "stored_file_name")
    op.drop_column("source_documents", "original_file_name")
    op.drop_column("source_documents", "source_kind")
