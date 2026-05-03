"""add error taxonomy annotations

Revision ID: 0012_error_taxonomy
Revises: 0011_review_workflow
Create Date: 2026-05-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012_error_taxonomy"
down_revision: Union[str, None] = "0011_review_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "error_annotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("test_question_id", sa.Integer(), nullable=False),
        sa.Column("generated_answer_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_record_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), server_default="human", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("evidence_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "category IN ('retrieval_miss', 'citation_error', 'hallucination', 'incomplete_answer', 'irrelevant_answer', 'contradiction', 'latency_cost', 'format_error', 'policy_ambiguity', 'other')",
            name="ck_error_annotations_category",
        ),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_error_annotations_severity"),
        sa.CheckConstraint("source IN ('human', 'automated')", name="ck_error_annotations_source"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluation_record_id"], ["evaluation_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_answer_id"], ["generated_answers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_question_id"], ["test_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_error_annotations_id"), "error_annotations", ["id"], unique=False)
    op.create_index(op.f("ix_error_annotations_evaluation_run_id"), "error_annotations", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_error_annotations_test_question_id"), "error_annotations", ["test_question_id"], unique=False)
    op.create_index(op.f("ix_error_annotations_generated_answer_id"), "error_annotations", ["generated_answer_id"], unique=False)
    op.create_index(op.f("ix_error_annotations_evaluation_record_id"), "error_annotations", ["evaluation_record_id"], unique=False)
    op.create_index(op.f("ix_error_annotations_created_by_user_id"), "error_annotations", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_error_annotations_created_by_user_id"), table_name="error_annotations")
    op.drop_index(op.f("ix_error_annotations_evaluation_record_id"), table_name="error_annotations")
    op.drop_index(op.f("ix_error_annotations_generated_answer_id"), table_name="error_annotations")
    op.drop_index(op.f("ix_error_annotations_test_question_id"), table_name="error_annotations")
    op.drop_index(op.f("ix_error_annotations_evaluation_run_id"), table_name="error_annotations")
    op.drop_index(op.f("ix_error_annotations_id"), table_name="error_annotations")
    op.drop_table("error_annotations")
