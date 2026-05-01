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
