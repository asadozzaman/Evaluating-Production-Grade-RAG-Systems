"""add background jobs

Revision ID: 0014_background_jobs
Revises: 0013_audit_events
Create Date: 2026-05-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_background_jobs"
down_revision: Union[str, None] = "0013_audit_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="queued", nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=120), nullable=True),
        sa.Column("input_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_background_jobs_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_background_jobs_id"), "background_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_background_jobs_job_type"), "background_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_background_jobs_status"), "background_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_background_jobs_project_id"), "background_jobs", ["project_id"], unique=False)
    op.create_index(op.f("ix_background_jobs_evaluation_run_id"), "background_jobs", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_background_jobs_requested_by_user_id"), "background_jobs", ["requested_by_user_id"], unique=False)
    op.create_index(op.f("ix_background_jobs_created_at"), "background_jobs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_background_jobs_created_at"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_requested_by_user_id"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_evaluation_run_id"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_project_id"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_status"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_job_type"), table_name="background_jobs")
    op.drop_index(op.f("ix_background_jobs_id"), table_name="background_jobs")
    op.drop_table("background_jobs")
