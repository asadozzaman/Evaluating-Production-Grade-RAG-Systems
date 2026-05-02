"""add evaluation run execution status

Revision ID: 0005_run_status
Revises: 0004_doc_sources
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_run_status"
down_revision: Union[str, None] = "0004_doc_sources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
    )
    op.add_column("evaluation_runs", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column(
        "evaluation_runs",
        sa.Column("processed_question_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_check_constraint(
        "ck_evaluation_runs_status",
        "evaluation_runs",
        "status IN ('pending', 'running', 'completed', 'failed')",
    )
    op.create_check_constraint(
        "ck_evaluation_runs_processed_question_count_non_negative",
        "evaluation_runs",
        "processed_question_count >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_evaluation_runs_processed_question_count_non_negative", "evaluation_runs", type_="check")
    op.drop_constraint("ck_evaluation_runs_status", "evaluation_runs", type_="check")
    op.drop_column("evaluation_runs", "processed_question_count")
    op.drop_column("evaluation_runs", "last_error")
    op.drop_column("evaluation_runs", "status")
