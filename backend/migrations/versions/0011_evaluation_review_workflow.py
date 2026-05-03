"""add evaluation review workflow

Revision ID: 0011_review_workflow
Revises: 0010_batch_fields
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011_review_workflow"
down_revision: Union[str, None] = "0010_batch_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_records",
        sa.Column("review_status", sa.String(length=30), server_default="pending_review", nullable=False),
    )
    op.add_column("evaluation_records", sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("evaluation_records", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("evaluation_records", sa.Column("review_notes", sa.Text(), nullable=True))
    op.add_column("evaluation_records", sa.Column("score_change_reason", sa.Text(), nullable=True))
    op.create_index(op.f("ix_evaluation_records_reviewed_by_user_id"), "evaluation_records", ["reviewed_by_user_id"], unique=False)
    op.create_foreign_key(
        "fk_evaluation_records_reviewed_by_user_id_users",
        "evaluation_records",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_evaluation_records_review_status",
        "evaluation_records",
        "review_status IN ('pending_review', 'approved', 'needs_revision')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_evaluation_records_review_status", "evaluation_records", type_="check")
    op.drop_constraint("fk_evaluation_records_reviewed_by_user_id_users", "evaluation_records", type_="foreignkey")
    op.drop_index(op.f("ix_evaluation_records_reviewed_by_user_id"), table_name="evaluation_records")
    op.drop_column("evaluation_records", "score_change_reason")
    op.drop_column("evaluation_records", "review_notes")
    op.drop_column("evaluation_records", "reviewed_at")
    op.drop_column("evaluation_records", "reviewed_by_user_id")
    op.drop_column("evaluation_records", "review_status")
