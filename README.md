# Smart Business Management and Tracking System

A full-stack platform for managing sales, inventory, employees, receipts, and business analytics.

## Overview

This project is split into:

- A FastAPI backend with JWT authentication, role-based access, validation, and reporting/export features.
- A React + Vite frontend dashboard for business operations.
- PostgreSQL as the primary relational datastore.
- MongoDB for additional data/document workflows.
- Docker Compose for consistent local containerized development.

## Quick Start

Choose one workflow:

- Local development (recommended for coding and debugging)
- Docker Compose (recommended for consistent environment setup)

For a full setup walkthrough, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

## Tech Stack

- Frontend: React 18, Vite, React Router, Axios, Chart.js/Recharts, Zustand, React Hook Form
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic Settings, JWT auth
- Databases: PostgreSQL 15, MongoDB 7
- Tooling: Docker, Docker Compose, PowerShell scripts

## Project Structure

```text
Main_pro_ject/
|-- frontend/            # React application
|-- backend/             # FastAPI application
|   |-- app/             # Routers, models, services, schemas
|   |-- alembic/         # Database migrations
|   `-- scripts/         # Utility scripts (e.g., admin creation)
|-- database/            # SQL bootstrap scripts
|-- docs/                # API documentation
`-- archive/             # Historical docs/scripts retained for reference
```

## Local Development

### 1. Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL
- MongoDB

### 2. Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DEBUG=True
HOST=0.0.0.0
PORT=8000

POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=business_management

MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=business_management

SECRET_KEY=replace-with-a-strong-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

Run backend:

```powershell
cd backend
.\venv\Scripts\activate
python main.py
```

### 3. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

By current Vite config, frontend runs on port `3000`.

## Docker Development

From the project root:

```powershell
docker-compose up -d
```

Useful commands:

```powershell
docker-compose ps
docker-compose logs -f
docker-compose down
docker-compose down -v
```

Container URLs:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Application URLs

Local (non-Docker):

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- Health endpoint: http://localhost:8000/api/health

## Database Migrations (Alembic)

Run Alembic from the `backend/` directory only.

Check current revision and upgrade:

```powershell
cd backend
.\venv\Scripts\activate
alembic current
alembic upgrade head
```

Create a new migration:

```powershell
cd backend
.\venv\Scripts\activate
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## Testing and Validation

Backend validation/test scripts are available in `backend/`.

Examples:

```powershell
cd backend
.\venv\Scripts\activate
python test_validation.py
python test_new_endpoints.py
python test_audit_system.py
```

## Utility Scripts

- Start backend and frontend in separate PowerShell windows: `start-servers.ps1`
- Create initial admin user: `backend/scripts/create_admin.py`

If admin is created through the script, default credentials are:

- Username: `admin`
- Password: `admin123`

Change the password immediately after first login.

## Documentation

- Setup and maintenance: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- API reference: [docs/API.md](docs/API.md)
- Backend DB setup notes: [backend/DATABASE_SETUP.md](backend/DATABASE_SETUP.md)
- Archive policy and restore guidance: [archive/README.md](archive/README.md)

## Troubleshooting

- Backend fails to start: verify `backend/.env` values and database availability.
- Frontend cannot reach API: check backend status and Vite proxy/API URL settings.
- Docker services unhealthy: inspect `docker-compose logs -f` and restart impacted containers.

## Notes

- Historical docs and one-off runbooks are stored under `archive/docs/`.
- One-off helper scripts are stored under `archive/scripts/`.


