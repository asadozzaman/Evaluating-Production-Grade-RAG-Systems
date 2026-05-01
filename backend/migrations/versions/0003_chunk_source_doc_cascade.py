"""cascade retrieved chunks when source documents are removed

Revision ID: 0003_chunk_source_cascade
Revises: 0002_core_tables
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0003_chunk_source_cascade"
down_revision: Union[str, None] = "0002_core_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "retrieved_chunks_source_document_id_fkey",
        "retrieved_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "retrieved_chunks_source_document_id_fkey",
        "retrieved_chunks",
        "source_documents",
        ["source_document_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "retrieved_chunks_source_document_id_fkey",
        "retrieved_chunks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "retrieved_chunks_source_document_id_fkey",
        "retrieved_chunks",
        "source_documents",
        ["source_document_id"],
        ["id"],
        ondelete="RESTRICT",
    )
