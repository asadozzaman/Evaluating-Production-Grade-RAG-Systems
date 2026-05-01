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
  app/
    auth.py
    config.py
    database.py
    main.py
    models.py
    schemas.py
    security.py
    routers/
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
