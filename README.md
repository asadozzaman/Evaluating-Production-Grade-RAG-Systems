# CLEAR-RAG

CLEAR-RAG is a practical evaluation platform for production-style retrieval-augmented generation (RAG) systems. It helps teams set up evaluation projects, upload and index source documents, import question datasets, run Gemini-powered RAG experiments, score answer quality, review failures, compare runs, and assess production readiness.

This repository contains:

- A FastAPI backend
- A Next.js frontend
- PostgreSQL via Docker Compose
- Authentication with role-based access control
- A full evaluation workflow for RAG experiments

For a non-technical walkthrough, see [CLEAR-RAG_User_Guide.md](./CLEAR-RAG_User_Guide.md).

## What CLEAR-RAG Does

CLEAR-RAG is designed to answer questions like:

- Did the retriever find the right evidence?
- Did the model answer using that evidence faithfully?
- Are automated judgments aligned with human review?
- Which experiment run is best?
- Is this RAG system ready for production use?

The platform supports:

- Project workspaces for separate RAG systems or use cases
- Source document upload and metadata management
- Document indexing for vector retrieval
- Manual question creation and dataset import from CSV or JSON
- Gemini RAG execution with keyword or vector retrieval
- Automated CLEAR-RAG scoring using an LLM-as-judge flow
- Human review and score override workflows
- Retrieval metrics such as hit rate, precision@k, recall@k, MRR, and chunk coverage
- Error taxonomy tagging for failed answers
- Experiment comparison and project leaderboard views
- Production readiness gates
- Report generation and data export
- Audit trail and governance summaries
- Background job tracking for long-running tasks

## Repository Structure

```text
.
|-- backend
|   |-- app
|   |   |-- routers
|   |   |-- services
|   |   |-- models.py
|   |   `-- schemas.py
|   |-- migrations
|   `-- tests
|-- frontend
|   `-- app
|-- CLEAR-RAG_User_Guide.md
|-- docker-compose.yml
`-- README.md
```

## Tech Stack

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- PyJWT
- `pwdlib` with Argon2 password hashing

### Frontend

- Next.js 15
- React 19
- TypeScript

### Model and Retrieval Services

- Gemini for generation and embedding calls
- Keyword retrieval over extracted document chunks
- Vector retrieval over stored embeddings

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop

### 1. Configure environment files

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.local.example frontend/.env.local
```

### 2. Start PostgreSQL

```powershell
docker compose up -d postgres
```

Default local database settings:

```text
Database: clearrag
User: clearrag
Password: clearrag
Host: localhost
Port: 5432
```

### 3. Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend health endpoint:

```text
http://localhost:8000/health
```

### 4. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend app:

```text
http://localhost:3000
```

## Authentication and Roles

CLEAR-RAG currently supports three base roles:

- `admin`
- `evaluator`
- `viewer`

Behavior currently implemented:

- The first registered user becomes `admin`
- Later registered users become `viewer`
- `admin` and `evaluator` can create and modify evaluation data
- `viewer` can read data only

Current auth endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /auth/admin-check`
- `GET /auth/evaluator-check`

## Typical Workflow

1. Create a project for a RAG system or use case.
2. Upload source documents.
3. Index uploaded documents if vector retrieval will be used.
4. Add individual test questions or import a dataset from CSV or JSON.
5. Create a run or launch a batch experiment.
6. Execute Gemini RAG with keyword or vector retrieval.
7. Review retrieved chunks and generated answers.
8. Run automated CLEAR-RAG evaluation.
9. Complete human review and approve or override scores.
10. Inspect retrieval metrics, judge calibration, error taxonomy, and readiness gates.
11. Compare runs, check the leaderboard, export results, or build a report.

## Key API Areas

### Project and setup

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`

- `POST /projects/{project_id}/documents`
- `POST /projects/{project_id}/documents/upload`
- `POST /projects/{project_id}/documents/{document_id}/index`
- `GET /projects/{project_id}/documents/{document_id}/chunks`

- `POST /projects/{project_id}/questions`
- `POST /projects/{project_id}/question-datasets/import`
- `GET /projects/{project_id}/question-datasets`

### Run execution and evaluation

- `POST /projects/{project_id}/runs`
- `POST /projects/{project_id}/runs/{run_id}/execute`
- `POST /projects/{project_id}/runs/{run_id}/auto-evaluate`
- `POST /projects/{project_id}/batch-experiments`

### Analytics and reporting

- `GET /projects/{project_id}/runs/{run_id}/summary`
- `GET /projects/{project_id}/runs/{run_id}/retrieval-metrics`
- `GET /projects/{project_id}/runs/{run_id}/review-dashboard`
- `GET /projects/{project_id}/runs/{run_id}/judge-calibration`
- `GET /projects/{project_id}/runs/{run_id}/error-taxonomy`
- `GET /projects/{project_id}/runs/{run_id}/production-readiness`
- `POST /projects/{project_id}/runs/{run_id}/report`
- `GET /projects/{project_id}/runs/{run_id}/export.json`
- `GET /projects/{project_id}/runs/{run_id}/export.csv`

### Project-level oversight

- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/leaderboard`
- `GET /projects/{project_id}/governance-summary`
- `GET /projects/{project_id}/runs/compare`

## Current Product Notes

The system is much more than a starter scaffold, but there are still a few important limitations to understand:

- URI-based source documents can be stored as references, but they are not currently extracted into searchable retrieval content by the backend.
- Vector retrieval works on uploaded and indexed files only.
- Background jobs are tracked in the database, but job execution currently uses in-process FastAPI background tasks rather than a separate durable worker system.
- Role promotion and user administration are not exposed as a full user-management feature in the current app.

These are good candidates for future hardening, but they do not change the fact that the core evaluation workflow is already implemented.

## Gemini Configuration

Set Gemini values in `backend/.env`:

```text
LLM_PROVIDER=gemini
DEFAULT_LLM_MODEL=gemini
DEFAULT_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_API_KEY=your-key-here
```

The health endpoint reports whether the backend can see a Gemini key without exposing the secret.

## Testing

### Backend

```powershell
cd backend
pytest -q
```

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

## Documentation Guidance

Use the files for different audiences:

- `README.md`: repository overview, architecture, setup, workflow, and current limitations
- `CLEAR-RAG_User_Guide.md`: non-technical end-user walkthrough

If you update product behavior, keep both files in sync.
