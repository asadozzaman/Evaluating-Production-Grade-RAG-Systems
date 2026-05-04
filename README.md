# CLEAR-RAG Project Foundation

This repository contains the foundation for a CLEAR-RAG evaluation tool. It includes a FastAPI backend, a Next.js frontend, PostgreSQL through Docker Compose, and Phase 2 authentication with role-based access control.

CLEAR-RAG evaluation business features are intentionally not implemented yet.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop

## Install Docker Desktop on Windows

If Docker Desktop is not installed, install it with `winget`:

```powershell
winget install --id Docker.DockerDesktop --exact --accept-source-agreements --accept-package-agreements
```

Start Docker Desktop after installation, then verify the CLI:

```powershell
docker --version
docker compose version
```

If `docker` is installed but PowerShell does not recognize the command, close and reopen the terminal. The Docker CLI is normally located at:

```text
C:\Program Files\Docker\Docker\resources\bin
```

## Environment Setup

Copy the example environment files:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.local.example frontend/.env.local
```

## Start PostgreSQL

Make sure Docker Desktop is running first.

```powershell
docker compose up -d postgres
```

PostgreSQL will be available at:

```text
localhost:5432
```

Default local credentials:

```text
Database: clearrag
User: clearrag
Password: clearrag
```

The backend uses the SQLAlchemy psycopg v3 driver:

```text
postgresql+psycopg://clearrag:clearrag@localhost:5432/clearrag
```

## Start the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Health check:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "CLEAR-RAG API",
  "environment": "development"
}
```

## Authentication

Phase 2 adds JWT authentication and three base roles:

```text
admin
evaluator
viewer
```

Run database migrations before using auth endpoints:

```powershell
cd backend
alembic upgrade head
```

The first registered user becomes `admin`. Later registered users become `viewer`.

Available auth endpoints:

```text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
GET  /auth/admin-check
GET  /auth/evaluator-check
```

Set a strong JWT secret in `backend/.env` before using anything beyond local development:

```text
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

## Gemini Configuration

The generated answer form stores the model name used for a manual test. Do not paste API keys into the browser. Keep the Gemini key in `backend/.env`:

```text
LLM_PROVIDER=gemini
DEFAULT_LLM_MODEL=gemini
DEFAULT_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_API_KEY=your-rotated-local-key
```

The health endpoint confirms whether the backend can see a Gemini key without returning the secret:

```text
http://localhost:8000/health
```

Expected fields:

```json
{
  "llm_provider": "gemini",
  "default_llm_model": "gemini",
  "gemini_configured": true
}
```

Gemini is called by the Phase 6 run execution endpoint. The manual generated answer form remains available for controlled evaluation data entry.

## Core Database Models

Phase 3 adds the relational foundation for CLEAR-RAG evaluation data. These models exist in the database layer only; full CRUD APIs and business workflows are intentionally deferred.

Core tables:

```text
projects
source_documents
test_questions
evaluation_runs
retrieved_chunks
generated_answers
evaluation_records
```

The schema stores the evaluation trail needed by CLEAR-RAG:

```text
Project -> documents, questions, evaluation runs
Evaluation run -> retrieved chunks, generated answers, evaluation records
Evaluation record -> reviewer and five CLEAR-RAG scores
```

Database constraints enforce the basic rubric and measurement rules:

```text
CLEAR-RAG scores must be between 1 and 5
Retrieved chunk rank must be greater than 0
Token counts, latency values, and estimated cost must be non-negative
Question type must be one of the supported evaluation question categories
Retrieved chunk relevance label must be high, medium, low, or irrelevant
```

Run migrations after pulling schema changes:

```powershell
cd backend
alembic upgrade head
```

## Project Setup APIs

Phase 4 adds authenticated setup APIs for preparing a CLEAR-RAG evaluation workspace. Admins and evaluators can create, update, and delete setup data. Viewers can read setup data only.

Project endpoints:

```text
POST   /projects
GET    /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
```

Nested setup endpoints:

```text
POST   /projects/{project_id}/documents
POST   /projects/{project_id}/documents/upload
GET    /projects/{project_id}/documents
GET    /projects/{project_id}/documents/{document_id}
PATCH  /projects/{project_id}/documents/{document_id}
DELETE /projects/{project_id}/documents/{document_id}

POST   /projects/{project_id}/questions
GET    /projects/{project_id}/questions
GET    /projects/{project_id}/questions/{question_id}
PATCH  /projects/{project_id}/questions/{question_id}
DELETE /projects/{project_id}/questions/{question_id}

POST   /projects/{project_id}/runs
GET    /projects/{project_id}/runs
GET    /projects/{project_id}/runs/{run_id}
PATCH  /projects/{project_id}/runs/{run_id}
DELETE /projects/{project_id}/runs/{run_id}
```

Frontend setup pages:

```text
/dashboard/projects
/dashboard/projects/new
/dashboard/projects/{projectId}
```

Phase 4 does not implement retrieved chunk submission, generated answer submission, CLEAR-RAG scoring, dashboards, CSV import/export, document parsing, embeddings, or RAG integration.

### Document Sources

Source documents can now be created in two ways:

```text
URI metadata: POST /projects/{project_id}/documents
File upload:  POST /projects/{project_id}/documents/upload
```

URI document JSON example:

```json
{
  "title": "HR Leave Policy",
  "document_type": "policy",
  "source_kind": "uri",
  "source_uri": "memory://hr-leave-policy",
  "version": "v1"
}
```

Upload documents use multipart form data:

```text
title
document_type
version
file
```

Supported upload extensions:

```text
.pdf, .docx, .txt, .csv, .md
```

Uploaded files are stored under:

```text
backend/uploads/documents/{project_id}/
```

This only stores the file and metadata. It does not extract text, parse documents, chunk content, create embeddings, or run retrieval yet.

## RAG Output Intake

Phase 5 adds APIs and a lightweight UI for recording raw RAG outputs before human scoring. Admins and evaluators can add and delete outputs. Viewers can read them only.

Retrieved chunk endpoints:

```text
POST   /projects/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks
GET    /projects/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks
DELETE /projects/{project_id}/runs/{run_id}/questions/{question_id}/retrieved-chunks/{chunk_id}
```

Generated answer endpoints:

```text
POST   /projects/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers
GET    /projects/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers
DELETE /projects/{project_id}/runs/{run_id}/questions/{question_id}/generated-answers/{answer_id}
```

Frontend run output page:

```text
/dashboard/projects/{projectId}/runs/{runId}
```

Use this page to select a test question, then record:

```text
retrieved chunks
generated answers
retrieval/generation timing
token counts
estimated cost
model name
```

Phase 5 does not implement CLEAR-RAG scoring, reviewer notes, score calculation, reports, automatic retrieval, embeddings, or LLM-assisted judging.

## Automatic Gemini RAG Execution

Phase 6 adds a basic automatic RAG execution path. Admins and evaluators can run Gemini RAG for an evaluation run:

```text
POST /projects/{project_id}/runs/{run_id}/execute
```

The execution currently:

```text
extracts text from uploaded .txt, .md, .csv, .docx, and .pdf files
splits document text into simple chunks
retrieves top chunks with keyword matching
calls Gemini using GEMINI_API_KEY from backend/.env
saves retrieved chunks and generated answers
updates run status as pending, running, completed, or failed
```

Frontend run page:

```text
/dashboard/projects/{projectId}/runs/{runId}
```

Click:

```text
Run Gemini RAG
```

This replaces previous retrieved chunks and generated answers for that run. URI-only documents are stored as metadata but are not fetched or parsed yet; upload a readable file when testing automatic RAG.

Phase 6 still uses simple keyword retrieval. Embeddings, vector search, production-grade retriever evaluation, and CLEAR-RAG human scoring are later phases.

## CLEAR-RAG Human Evaluation Scoring

Phase 7 adds evaluator scoring for generated answers. Admins and evaluators can score each answer on the five CLEAR-RAG dimensions:

```text
Citation Quality
Latency and Cost Efficiency
Evidence Faithfulness
Answer Relevance
Retrieval Quality
```

Scores use a 1-5 scale. The backend calculates the overall score automatically:

```text
overall_score = average of the five dimension scores
```

Evaluation endpoints:

```text
POST   /projects/{project_id}/runs/{run_id}/questions/{question_id}/answers/{answer_id}/evaluations
GET    /projects/{project_id}/runs/{run_id}/evaluations
PATCH  /projects/{project_id}/runs/{run_id}/evaluations/{evaluation_id}
DELETE /projects/{project_id}/runs/{run_id}/evaluations/{evaluation_id}
```

The run page now shows a CLEAR-RAG scoring form under generated answers:

```text
/dashboard/projects/{projectId}/runs/{runId}
```

Viewers can read scores but cannot create, update, or delete them.

## Evaluation Reports and Analytics

Phase 8 adds run and project summaries so evaluation data can be interpreted without manually reading every record.

Run summary endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/summary
```

Project summary endpoint:

```text
GET /projects/{project_id}/summary
```

Run export endpoints:

```text
GET /projects/{project_id}/runs/{run_id}/export.csv
GET /projects/{project_id}/runs/{run_id}/export.json
```

The run page now shows:

```text
total questions
generated answers
reviewed answers
review completion percentage
average overall score
average score by CLEAR-RAG dimension
weakest dimension
question-level results
CSV and JSON export buttons
```

## Document Indexing and Vector Retrieval

Phase 9 adds an embedding-backed retrieval path while keeping keyword retrieval available.

Index a file-based source document:

```text
POST /projects/{project_id}/documents/{document_id}/index
```

Read indexed chunks:

```text
GET /projects/{project_id}/documents/{document_id}/chunks
```

Run Gemini RAG with vector retrieval:

```text
POST /projects/{project_id}/runs/{run_id}/execute
```

Request body:

```json
{
  "retrieval_mode": "vector"
}
```

The frontend flow is:

```text
1. Upload a readable .txt, .md, .csv, .docx, or .pdf document.
2. Click Index for vector search on the project setup page.
3. Open a run.
4. Select Vector embeddings as the retrieval mode.
5. Click Run Gemini RAG.
```

Embeddings are stored in PostgreSQL as persistent document chunks, and retrieval uses cosine similarity in the backend. The current Docker service remains the standard PostgreSQL image; pgvector can be added later as a production hardening step.

## Automated CLEAR-RAG Evaluation

Phase 10 adds LLM-as-judge scoring for generated answers. Admins and evaluators can run automated CLEAR-RAG evaluation after a run has generated answers:

```text
POST /projects/{project_id}/runs/{run_id}/auto-evaluate
```

The judge reads:

```text
test question
expected source
retrieved chunks
generated answer
token, latency, and cost metadata
```

It stores an evaluation record with:

```text
Citation Quality score
Latency and Cost Efficiency score
Evidence Faithfulness score
Answer Relevance score
Retrieval Quality score
overall score
judge model name
judge reasoning
reviewer notes
suggested improvement
evaluation mode: automated
```

The frontend run page now includes:

```text
Run Automated CLEAR-RAG Evaluation
```

Human scoring still works. Human records use `evaluation_mode: human`; automated records use `evaluation_mode: automated`, so reports can distinguish the source of a score.

## Experiment Comparison and Benchmarking

Phase 11 adds run comparison for benchmarking RAG experiments inside a project.

Compare two or more runs:

```text
GET /projects/{project_id}/runs/compare?run_ids={run_id_a}&run_ids={run_id_b}
```

The comparison returns:

```text
run metadata
retrieval mode
generator model
embedding model
judge model
generated and reviewed answer counts
average overall score
dimension averages
weakest dimension
score deltas against the baseline run
question-level answers and best run
```

The project page now includes a Run Comparison panel. Select at least two runs, click Compare selected runs, and review the side-by-side scores and question-level differences.

Run execution now persists experiment metadata on the run:

```text
retrieval_mode
generator_model_name
embedding_model_name
judge_model_name
```

## Dataset Import and Batch Evaluation

Phase 12 adds repeatable question dataset imports so larger evaluation sets do not need to be entered one question at a time.

Import CSV or JSON questions:

```text
POST /projects/{project_id}/question-datasets/import
```

Multipart form fields:

```text
dataset_name
dataset_version
file
```

CSV format:

```csv
question_text,question_type,expected_source
How many annual leave days are provided?,simple_factual,HR Leave Policy
When is a medical certificate required?,conditional,HR Leave Policy
How much leave can be carried forward?,simple_factual,HR Leave Policy
```

JSON format:

```json
{
  "questions": [
    {
      "question_text": "How many annual leave days are provided?",
      "question_type": "simple_factual",
      "expected_source": "HR Leave Policy"
    }
  ]
}
```

Supported question types:

```text
simple_factual
conditional
multi_document
ambiguous
edge_case
```

List imported datasets:

```text
GET /projects/{project_id}/question-datasets
```

The import response reports:

```text
questions_imported
duplicate_questions
invalid_rows
row-level errors
dataset metadata
```

The frontend project page now includes a question-set import form in the Questions section.

## Batch Experiment Orchestration

Phase 13 adds a single endpoint and frontend panel for running a full dataset-based experiment.

Run a batch experiment:

```text
POST /projects/{project_id}/batch-experiments
```

JSON body:

```json
{
  "run_name": "Nightly Batch Evaluation",
  "dataset_id": 1,
  "document_ids": [47],
  "retrieval_mode": "keyword",
  "system_version": "batch-v1",
  "notes": "Regression test against uploaded HR policy",
  "index_documents": false,
  "auto_evaluate": true
}
```

The batch workflow:

```text
validates the selected question dataset
validates selected source documents
creates a new evaluation run
optionally indexes selected documents for vector retrieval
runs Gemini RAG only for the selected dataset and documents
optionally runs automated CLEAR-RAG judging
saves batch status, current step, completed steps, and errors on the run
returns the run, RAG execution result, automated evaluation result, and summary
```

Frontend flow:

```text
1. Open /dashboard/projects/{projectId}.
2. Upload a readable document.
3. Import a CSV or JSON question dataset.
4. In Batch Experiment, choose the dataset and document.
5. Select keyword or vector retrieval.
6. Keep automated CLEAR-RAG evaluation enabled if Gemini judging should run.
7. Click Run Batch Experiment.
8. Open the created run from the Runs list to inspect chunks, answers, scores, and exports.
```

## Evaluation Review Workflow

Phase 14 adds human review controls for automated CLEAR-RAG results.

Review dashboard endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/review-dashboard
```

The dashboard returns:

```text
all generated answers for the run
question and expected source
generated answer text
retrieved evidence chunks
latest CLEAR-RAG scores
judge reasoning
review status
approved/pending/needs-revision counts
ready_for_release quality gate
approved average score
```

Review or override an evaluation:

```text
PATCH /projects/{project_id}/runs/{run_id}/evaluations/{evaluation_id}/review
```

Example approve request:

```json
{
  "review_status": "approved",
  "review_notes": "Automated score is acceptable for reporting."
}
```

Example score override request:

```json
{
  "review_status": "needs_revision",
  "citation_quality_score": 3,
  "review_notes": "Citation points to the right document but not the exact policy section.",
  "score_change_reason": "Human reviewer found the citation less specific than the automated judge rated."
}
```

Review statuses:

```text
pending_review
approved
needs_revision
```

The run page now includes an Evaluation Review panel. A run is marked ready only when every generated answer has an approved evaluation.

## Advanced Retrieval Evaluation

Phase 15 adds retrieval-specific metrics so the system can evaluate whether the retriever found the right evidence before judging generated answers.

Retrieval metrics endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/retrieval-metrics
```

The metrics are also included inside:

```text
GET /projects/{project_id}/runs/{run_id}/summary
GET /projects/{project_id}/runs/{run_id}/export.json
GET /projects/{project_id}/runs/{run_id}/export.csv
```

The backend compares each question's `expected_source` with the ranked retrieved chunks using the source document title, source URI, section reference, and chunk text.

Run-level metrics:

```text
hit_rate
precision_at_k
recall_at_k
mean_reciprocal_rank
chunk_coverage
missing_evidence_count
expected_source_hit_count
```

Question-level metrics:

```text
expected_source_match
first_relevant_rank
retrieved_chunk_count
relevant_chunk_count
precision_at_k
recall_at_k
reciprocal_rank
missing_evidence
```

The run page now shows a Retrieval Metrics section inside Evaluation Summary, including hit rate, Precision@3, Recall@3, MRR, chunk coverage, and missing evidence.

## Judge Calibration and Human Agreement

Phase 16 compares automated CLEAR-RAG judge scores with human CLEAR-RAG scores for the same generated answer.

Calibration endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/judge-calibration
```

The report returns:

```text
paired_answer_count
automated_only_count
human_only_count
overall_exact_agreement_percent
overall_within_one_agreement_percent
average_overall_delta
dimension_calibration
answer_comparisons
```

How pairing works:

```text
1. Run automated CLEAR-RAG evaluation for generated answers.
2. Add a human CLEAR-RAG score for the same answer.
3. The calibration report pairs the latest automated score with the latest approved human score.
4. Deltas are calculated as human score minus automated score.
```

Bias direction:

```text
aligned: average human and automated scores match
automated_under_scores: human scores are higher than automated scores
automated_over_scores: automated scores are higher than human scores
```

The run page now includes a Judge Calibration panel with paired answers, exact agreement, within-one-point agreement, average score delta, dimension bias, and answer-level comparisons.

## Error Taxonomy

Phase 17 adds structured error tagging so evaluators can classify why a RAG answer failed.

Taxonomy summary endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/error-taxonomy
```

Create an error tag for an answer:

```text
POST /projects/{project_id}/runs/{run_id}/questions/{question_id}/answers/{answer_id}/errors
```

Example request:

```json
{
  "category": "citation_error",
  "severity": "high",
  "evaluation_record_id": 83,
  "notes": "Answer cites the policy document but not the exact leave section.",
  "evidence_reference": "Expected Section 1.1"
}
```

Supported categories:

```text
retrieval_miss
citation_error
hallucination
incomplete_answer
irrelevant_answer
contradiction
latency_cost
format_error
policy_ambiguity
other
```

Supported severities:

```text
low
medium
high
critical
```

The run page now includes an Error Taxonomy panel and an Add error tag form under each generated answer.

## Experiment Leaderboard

Phase 18 adds a project-level leaderboard for ranking RAG experiment runs.

Leaderboard endpoint:

```text
GET /projects/{project_id}/leaderboard
```

The leaderboard ranks runs using:

```text
CLEAR-RAG average score
review completion
retrieval hit rate
judge calibration within-one agreement
error taxonomy penalties
```

Each run includes:

```text
rank
leaderboard_score
quality_gate
generated_answers
reviewed_answers
approved_average_overall_score
retrieval_hit_rate
retrieval_mrr
judge agreement metrics
error counts
model and retrieval metadata
```

Quality gate values:

```text
no_outputs
blocked_critical_errors
needs_error_review
needs_review
release_candidate
scored
```

The project page now includes an Experiment Leaderboard panel above Run Comparison.

## Production Readiness Gates

Phase 19 adds a run-level readiness checklist for deciding whether an experiment is safe to release.

Readiness endpoint:

```text
GET /projects/{project_id}/runs/{run_id}/production-readiness
```

Required gates:

```text
run_completed
answer_coverage
human_review_complete
minimum_score
retrieval_hit_rate
missing_evidence
judge_calibration
blocking_errors
```

Default thresholds:

```text
minimum approved score: >= 4.00
retrieval hit rate: >= 0.80
judge within-one agreement: >= 80.00% with at least one paired answer
high/critical errors: 0
missing evidence: 0
```

The endpoint returns `ready_for_production`, gate counts, and detailed gate messages. The run page now includes a Production Readiness panel before review and calibration details.

## Report Builder

Phase 20 adds a run-level report builder that assembles the current evaluation state into a structured response and Markdown report.

Report endpoint:

```text
POST /projects/{project_id}/runs/{run_id}/report
```

Example request:

```json
{
  "title": "HR Policy RAG Release Report",
  "audience": "executive",
  "sections": ["overview", "readiness", "scores", "retrieval", "calibration", "errors", "questions"]
}
```

Supported audiences:

```text
executive
technical
audit
```

Supported sections:

```text
overview
readiness
scores
retrieval
calibration
errors
questions
```

The run page now includes a Report Builder panel that generates a Markdown report from the latest run metrics, readiness gates, calibration data, and error taxonomy.

## Audit Trail and Governance

Phase 21 adds project-level audit events and a governance summary for tracking who changed evaluation setup, outputs, reviews, error tags, and generated reports.

Audit endpoints:

```text
GET /projects/{project_id}/audit-events
GET /projects/{project_id}/runs/{run_id}/audit-events
GET /projects/{project_id}/governance-summary
```

Governance summary response includes:

```json
{
  "project_id": 47,
  "project_name": "HR Policy RAG Assistant",
  "total_events": 12,
  "active_actor_count": 2,
  "run_event_count": 7,
  "event_type_counts": [
    { "key": "report_built", "count": 2 }
  ],
  "entity_type_counts": [
    { "key": "evaluation_run", "count": 3 }
  ],
  "recent_events": []
}
```

The project page now includes an Audit Trail and Governance panel with event counts, active actors, and recent activity.

## Start the Frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```text
http://localhost:3000
```

## Project Structure

```text
backend/
  migrations/
    versions/
  app/
    auth.py
    config.py
    database.py
    main.py
    models.py
    schemas.py
    security.py
    routers/
      auth.py
      projects.py
  .env.example
  alembic.ini
  requirements.txt
frontend/
  app/
    dashboard/
    lib/
    login/
    register/
    globals.css
    layout.tsx
    page.tsx
  .env.local.example
  package.json
docker-compose.yml
README.md
```
