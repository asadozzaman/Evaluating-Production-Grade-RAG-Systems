"""create core evaluation tables

Revision ID: 0002_core_tables
Revises: 0001_create_auth_tables
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_core_tables"
down_revision: Union[str, None] = "0001_create_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_type", sa.String(length=100), nullable=False),
        sa.Column("target_users", sa.String(length=255), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("source_uri", sa.String(length=500), nullable=True),
        sa.Column("version", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_documents_id"), "source_documents", ["id"], unique=False)
    op.create_index(op.f("ix_source_documents_project_id"), "source_documents", ["project_id"], unique=False)
    op.create_index(op.f("ix_source_documents_title"), "source_documents", ["title"], unique=False)

    op.create_table(
        "test_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("expected_source", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "question_type IN ('simple_factual', 'conditional', 'multi_document', 'ambiguous', 'edge_case')",
            name="ck_test_questions_question_type",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_questions_id"), "test_questions", ["id"], unique=False)
    op.create_index(op.f("ix_test_questions_project_id"), "test_questions", ["project_id"], unique=False)
    op.create_index(op.f("ix_test_questions_question_type"), "test_questions", ["question_type"], unique=False)

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("system_version", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_runs_id"), "evaluation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_runs_project_id"), "evaluation_runs", ["project_id"], unique=False)

    op.create_table(
        "retrieved_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("test_question_id", sa.Integer(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("section_reference", sa.String(length=255), nullable=True),
        sa.Column("relevance_label", sa.String(length=50), nullable=True),
        sa.Column("retrieval_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rank > 0", name="ck_retrieved_chunks_rank_positive"),
        sa.CheckConstraint(
            "retrieval_time_ms IS NULL OR retrieval_time_ms >= 0",
            name="ck_retrieved_chunks_retrieval_time_non_negative",
        ),
        sa.CheckConstraint(
            "relevance_label IS NULL OR relevance_label IN ('high', 'medium', 'low', 'irrelevant')",
            name="ck_retrieved_chunks_relevance_label",
        ),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["test_question_id"], ["test_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retrieved_chunks_evaluation_run_id"), "retrieved_chunks", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_retrieved_chunks_id"), "retrieved_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_retrieved_chunks_source_document_id"), "retrieved_chunks", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_retrieved_chunks_test_question_id"), "retrieved_chunks", ["test_question_id"], unique=False)

    op.create_table(
        "generated_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("test_question_id", sa.Integer(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_time_ms", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="ck_generated_answers_input_tokens_non_negative",
        ),
        sa.CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="ck_generated_answers_output_tokens_non_negative",
        ),
        sa.CheckConstraint(
            "generation_time_ms IS NULL OR generation_time_ms >= 0",
            name="ck_generated_answers_generation_time_non_negative",
        ),
        sa.CheckConstraint(
            "estimated_cost IS NULL OR estimated_cost >= 0",
            name="ck_generated_answers_estimated_cost_non_negative",
        ),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_question_id"], ["test_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_answers_evaluation_run_id"), "generated_answers", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_generated_answers_id"), "generated_answers", ["id"], unique=False)
    op.create_index(op.f("ix_generated_answers_test_question_id"), "generated_answers", ["test_question_id"], unique=False)

    op.create_table(
        "evaluation_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluation_run_id", sa.Integer(), nullable=False),
        sa.Column("test_question_id", sa.Integer(), nullable=False),
        sa.Column("generated_answer_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=False),
        sa.Column("citation_quality_score", sa.Integer(), nullable=False),
        sa.Column("latency_cost_score", sa.Integer(), nullable=False),
        sa.Column("evidence_faithfulness_score", sa.Integer(), nullable=False),
        sa.Column("answer_relevance_score", sa.Integer(), nullable=False),
        sa.Column("retrieval_quality_score", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("suggested_improvement", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "citation_quality_score BETWEEN 1 AND 5",
            name="ck_evaluation_records_citation_quality_score",
        ),
        sa.CheckConstraint("latency_cost_score BETWEEN 1 AND 5", name="ck_evaluation_records_latency_cost_score"),
        sa.CheckConstraint(
            "evidence_faithfulness_score BETWEEN 1 AND 5",
            name="ck_evaluation_records_evidence_faithfulness_score",
        ),
        sa.CheckConstraint(
            "answer_relevance_score BETWEEN 1 AND 5",
            name="ck_evaluation_records_answer_relevance_score",
        ),
        sa.CheckConstraint(
            "retrieval_quality_score BETWEEN 1 AND 5",
            name="ck_evaluation_records_retrieval_quality_score",
        ),
        sa.CheckConstraint("overall_score BETWEEN 1 AND 5", name="ck_evaluation_records_overall_score"),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_answer_id"], ["generated_answers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["test_question_id"], ["test_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_records_evaluation_run_id"), "evaluation_records", ["evaluation_run_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_generated_answer_id"), "evaluation_records", ["generated_answer_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_id"), "evaluation_records", ["id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_reviewer_user_id"), "evaluation_records", ["reviewer_user_id"], unique=False)
    op.create_index(op.f("ix_evaluation_records_test_question_id"), "evaluation_records", ["test_question_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_records_test_question_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_reviewer_user_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_generated_answer_id"), table_name="evaluation_records")
    op.drop_index(op.f("ix_evaluation_records_evaluation_run_id"), table_name="evaluation_records")
    op.drop_table("evaluation_records")

    op.drop_index(op.f("ix_generated_answers_test_question_id"), table_name="generated_answers")
    op.drop_index(op.f("ix_generated_answers_id"), table_name="generated_answers")
    op.drop_index(op.f("ix_generated_answers_evaluation_run_id"), table_name="generated_answers")
    op.drop_table("generated_answers")

    op.drop_index(op.f("ix_retrieved_chunks_test_question_id"), table_name="retrieved_chunks")
    op.drop_index(op.f("ix_retrieved_chunks_source_document_id"), table_name="retrieved_chunks")
    op.drop_index(op.f("ix_retrieved_chunks_id"), table_name="retrieved_chunks")
    op.drop_index(op.f("ix_retrieved_chunks_evaluation_run_id"), table_name="retrieved_chunks")
    op.drop_table("retrieved_chunks")

    op.drop_index(op.f("ix_evaluation_runs_project_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_id"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    op.drop_index(op.f("ix_test_questions_question_type"), table_name="test_questions")
    op.drop_index(op.f("ix_test_questions_project_id"), table_name="test_questions")
    op.drop_index(op.f("ix_test_questions_id"), table_name="test_questions")
    op.drop_table("test_questions")

    op.drop_index(op.f("ix_source_documents_title"), table_name="source_documents")
    op.drop_index(op.f("ix_source_documents_project_id"), table_name="source_documents")
    op.drop_index(op.f("ix_source_documents_id"), table_name="source_documents")
    op.drop_table("source_documents")

    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_index(op.f("ix_projects_id"), table_name="projects")
    op.drop_table("projects")
