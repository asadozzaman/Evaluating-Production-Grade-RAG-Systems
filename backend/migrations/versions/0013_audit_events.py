"""add audit trail events

Revision ID: 0013_audit_events
Revises: 0012_error_taxonomy
Create Date: 2026-05-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_audit_events"
down_revision: Union[str, None] = "0012_error_taxonomy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=True),
        sa.Column("test_question_id", sa.Integer(), nullable=True),
        sa.Column("generated_answer_id", sa.Integer(), nullable=True),
        sa.Column("evaluation_record_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("event_summary", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_id"), "audit_events", ["id"], unique=False)
    op.create_index(op.f("ix_audit_events_actor_user_id"), "audit_events", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_events_project_id"), "audit_events", ["project_id"], unique=False)
    op.create_index(op.f("ix_audit_events_evaluation_run_id"), "audit_events", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_audit_events_test_question_id"), "audit_events", ["test_question_id"], unique=False)
    op.create_index(op.f("ix_audit_events_generated_answer_id"), "audit_events", ["generated_answer_id"], unique=False)
    op.create_index(op.f("ix_audit_events_evaluation_record_id"), "audit_events", ["evaluation_record_id"], unique=False)
    op.create_index(op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_audit_events_entity_type"), "audit_events", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_events_entity_id"), "audit_events", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_events_created_at"), "audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_created_at"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_entity_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_evaluation_record_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_generated_answer_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_test_question_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_evaluation_run_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_project_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_user_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_id"), table_name="audit_events")
    op.drop_table("audit_events")
