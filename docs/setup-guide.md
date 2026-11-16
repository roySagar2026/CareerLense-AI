# Local setup (Windows + VS Code)

## Prerequisites

- **Python 3.12** (python.org installer, tick "Add python.exe to PATH")
- **Node.js 22 LTS** (nodejs.org)
- **Git**
- VS Code with the recommended extensions (VS Code will offer them from `.vscode/extensions.json`)
- Docker Desktop (optional, only for the Docker route)

No database server is needed for local development: the backend falls back to a SQLite file.

## Option A — one script

Open PowerShell in the repository folder:

```powershell
./infrastructure/scripts/setup-windows.ps1
```

## Option B — manual

```powershell
# 1. environment file
Copy-Item .env.example .env

# 2. backend
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
# local SQLite database (no Postgres required): leave DATABASE_URL as sqlite in .env, or
$env:DATABASE_URL = "sqlite:///./careerlens.db"
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
# 3. frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to `http://localhost:8000`, so cookies work without CORS. API docs: http://localhost:8000/api/docs.

> Commit `frontend/package-lock.json` after your first `npm install` so CI and Docker get reproducible installs.

## Using Postgres locally

```powershell
docker compose up -d db
$env:DATABASE_URL = "postgresql://careerlens:<POSTGRES_PASSWORD from .env>@localhost:5432/careerlens"
cd backend; alembic upgrade head
```

Or run everything with `docker compose up --build` (see `docker-compose.yml`; web on http://localhost:8080).

## Tests and quality checks

```powershell
# backend (from backend/, venv active)
ruff check .
ruff format --check .
pytest --cov=app

# frontend (from frontend/)
npm run lint
npm run typecheck
npm test
npm run build

# end-to-end (API + dev server running, see .github/workflows/e2e.yml)
npx playwright install chromium
npm run e2e
```

Set `TEST_DATABASE_URL` to run the backend tests against Postgres instead of in-memory SQLite.

## Troubleshooting

- `Activate.ps1 cannot be loaded`: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- PyMuPDF fails to install: use Python 3.12 (64-bit); the PDF path falls back to `pypdf` automatically if PyMuPDF is unavailable.
- Port 8000/5173 busy: change `--port`, and the proxy target in `frontend/vite.config.ts`.
