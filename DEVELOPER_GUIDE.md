# Developer Guide

This is the single authoritative development guide for local setup, running, and maintenance.

## 1. Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL
- MongoDB
- Docker Desktop (optional, for container workflow)

## 2. Local Development (Non-Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` and set:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=business_management

MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=business_management

SECRET_KEY=replace-me
```

Run backend:

```bash
python main.py
```

Backend URLs:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:
- App: http://localhost:3000 (or Vite assigned port)

## 3. Docker Development

From project root:

```bash
docker-compose up -d
```

Useful commands:

```bash
docker-compose ps
docker-compose logs -f
docker-compose down
docker-compose down -v
```

Container URLs:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## 4. Database Notes

- PostgreSQL schema bootstrap: `database/init.sql`
- Backend-specific setup notes: `backend/DATABASE_SETUP.md`

## 5. Testing

Backend test/validation scripts currently live in `backend/`.
Run with the backend virtual environment activated, for example:

```bash
cd backend
python test_validation.py
python test_new_endpoints.py
```

## 6. Project Layout (Core)

- `frontend/` React application
- `backend/` FastAPI application
- `database/` SQL initialization scripts
- `docs/API.md` API reference

## 7. Cleanup and Archive Policy

- Active, operational docs stay at root only when needed for onboarding.
- Historical notes, status snapshots, and one-off runbooks are moved to `archive/docs/`.
- One-off debug/admin helper scripts are moved to `archive/scripts/`.
- Archive index and restore guidance: `archive/README.md`.

## 8. Troubleshooting Quick Checks

- Backend not starting: validate `backend/.env` and database services.
- Frontend API errors: verify backend is running and CORS/API URL configuration.
- Docker issues: inspect `docker-compose logs -f` and restart impacted services.
