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
