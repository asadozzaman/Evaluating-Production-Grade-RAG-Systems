"""add run experiment metadata

Revision ID: 0008_run_metadata
Revises: 0007_auto_eval_fields
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_run_metadata"
down_revision: Union[str, None] = "0007_auto_eval_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("retrieval_mode", sa.String(length=30), nullable=True))
    op.add_column("evaluation_runs", sa.Column("generator_model_name", sa.String(length=120), nullable=True))
    op.add_column("evaluation_runs", sa.Column("embedding_model_name", sa.String(length=120), nullable=True))
    op.add_column("evaluation_runs", sa.Column("judge_model_name", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluation_runs", "judge_model_name")
    op.drop_column("evaluation_runs", "embedding_model_name")
    op.drop_column("evaluation_runs", "generator_model_name")
    op.drop_column("evaluation_runs", "retrieval_mode")
