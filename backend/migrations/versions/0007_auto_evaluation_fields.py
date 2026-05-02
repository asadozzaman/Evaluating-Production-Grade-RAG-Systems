"""add automated evaluation audit fields

Revision ID: 0007_auto_eval_fields
Revises: 0006_document_chunks
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_auto_eval_fields"
down_revision: Union[str, None] = "0006_document_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_records",
        sa.Column("evaluation_mode", sa.String(length=30), server_default="human", nullable=False),
    )
    op.add_column("evaluation_records", sa.Column("judge_model_name", sa.String(length=120), nullable=True))
    op.add_column("evaluation_records", sa.Column("judge_reasoning", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_evaluation_records_evaluation_mode",
        "evaluation_records",
        "evaluation_mode IN ('human', 'automated')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_evaluation_records_evaluation_mode", "evaluation_records", type_="check")
    op.drop_column("evaluation_records", "judge_reasoning")
    op.drop_column("evaluation_records", "judge_model_name")
    op.drop_column("evaluation_records", "evaluation_mode")
