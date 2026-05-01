# CLEAR-RAG Project Foundation

This repository contains the initial foundation for a CLEAR-RAG evaluation tool. It includes a FastAPI backend, a Next.js frontend, and a PostgreSQL service managed by Docker Compose.

Business features are intentionally not implemented yet.

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

## Start the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
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
  app/
    config.py
    main.py
  .env.example
  requirements.txt
frontend/
  app/
    globals.css
    layout.tsx
    page.tsx
  .env.local.example
  package.json
docker-compose.yml
README.md
```
