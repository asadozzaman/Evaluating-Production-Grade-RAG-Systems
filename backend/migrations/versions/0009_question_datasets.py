"""add question datasets

Revision ID: 0009_question_datasets
Revises: 0008_run_metadata
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_question_datasets"
down_revision: Union[str, None] = "0008_run_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("dataset_version", sa.String(length=80), nullable=True),
        sa.Column("imported_file_name", sa.String(length=255), nullable=True),
        sa.Column("question_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("question_count >= 0", name="ck_question_datasets_question_count_non_negative"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_datasets_dataset_name"), "question_datasets", ["dataset_name"], unique=False)
    op.create_index(op.f("ix_question_datasets_id"), "question_datasets", ["id"], unique=False)
    op.create_index(op.f("ix_question_datasets_project_id"), "question_datasets", ["project_id"], unique=False)
    op.add_column("test_questions", sa.Column("dataset_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_test_questions_dataset_id"), "test_questions", ["dataset_id"], unique=False)
    op.create_foreign_key(
        "fk_test_questions_dataset_id_question_datasets",
        "test_questions",
        "question_datasets",
        ["dataset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_test_questions_dataset_id_question_datasets", "test_questions", type_="foreignkey")
    op.drop_index(op.f("ix_test_questions_dataset_id"), table_name="test_questions")
    op.drop_column("test_questions", "dataset_id")
    op.drop_index(op.f("ix_question_datasets_project_id"), table_name="question_datasets")
    op.drop_index(op.f("ix_question_datasets_id"), table_name="question_datasets")
    op.drop_index(op.f("ix_question_datasets_dataset_name"), table_name="question_datasets")
    op.drop_table("question_datasets")
