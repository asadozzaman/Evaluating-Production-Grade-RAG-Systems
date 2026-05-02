"""add batch experiment fields

Revision ID: 0010_batch_fields
Revises: 0009_question_datasets
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_batch_fields"
down_revision: Union[str, None] = "0009_question_datasets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("dataset_id", sa.Integer(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("batch_document_ids", sa.Text(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("auto_evaluate_enabled", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("evaluation_runs", sa.Column("batch_status", sa.String(length=30), nullable=True))
    op.add_column("evaluation_runs", sa.Column("current_step", sa.String(length=80), nullable=True))
    op.add_column("evaluation_runs", sa.Column("completed_steps", sa.Text(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("failed_step", sa.String(length=80), nullable=True))
    op.add_column("evaluation_runs", sa.Column("batch_error_message", sa.Text(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("batch_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("evaluation_runs", sa.Column("batch_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_evaluation_runs_dataset_id"), "evaluation_runs", ["dataset_id"], unique=False)
    op.create_foreign_key(
        "fk_evaluation_runs_dataset_id_question_datasets",
        "evaluation_runs",
        "question_datasets",
        ["dataset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_evaluation_runs_dataset_id_question_datasets", "evaluation_runs", type_="foreignkey")
    op.drop_index(op.f("ix_evaluation_runs_dataset_id"), table_name="evaluation_runs")
    op.drop_column("evaluation_runs", "batch_completed_at")
    op.drop_column("evaluation_runs", "batch_started_at")
    op.drop_column("evaluation_runs", "batch_error_message")
    op.drop_column("evaluation_runs", "failed_step")
    op.drop_column("evaluation_runs", "completed_steps")
    op.drop_column("evaluation_runs", "current_step")
    op.drop_column("evaluation_runs", "batch_status")
    op.drop_column("evaluation_runs", "auto_evaluate_enabled")
    op.drop_column("evaluation_runs", "batch_document_ids")
    op.drop_column("evaluation_runs", "dataset_id")
