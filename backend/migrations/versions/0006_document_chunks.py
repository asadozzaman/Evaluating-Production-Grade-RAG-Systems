"""add persistent document chunks

Revision ID: 0006_document_chunks
Revises: 0005_run_status
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_document_chunks"
down_revision: Union[str, None] = "0005_run_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("section_reference", sa.String(length=255), nullable=True),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("chunk_index > 0", name="ck_document_chunks_chunk_index_positive"),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_chunks_id"), "document_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_document_chunks_source_document_id"), "document_chunks", ["source_document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_source_document_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
