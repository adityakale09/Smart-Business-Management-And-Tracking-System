# Docker Quick Start Guide

## Prerequisites
- Docker Desktop installed and running
- At least 4GB RAM available for Docker

## Quick Start

### 1. Start All Services
```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Backend API (port 8000)
- Frontend (port 5173)

### 2. Check Status
```bash
docker-compose ps
```

### 3. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f mongodb
```

### 4. Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### 5. Stop All Services
```bash
docker-compose down
```

### 6. Stop and Remove All Data
```bash
docker-compose down -v
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
POSTGRES_PASSWORD=your_secure_password
MONGODB_PASSWORD=your_mongodb_password

# Security
SECRET_KEY=your-very-secret-key-here-change-this-in-production

# Optional
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Initialization

The PostgreSQL database will be automatically initialized with the schema from `database/init.sql` on first run.

To create an admin user:
```bash
docker-compose exec backend python scripts/create_admin.py
```

## Development Mode

The containers are set up with volume mounts for hot-reloading:
- Backend: Changes to Python files will auto-reload
- Frontend: Changes to React files will auto-reload

## Production Deployment

For production, modify `docker-compose.yml`:
1. Remove `--reload` from backend command
2. Build frontend for production
3. Use environment-specific .env files
4. Add nginx reverse proxy
5. Set up SSL/TLS certificates

## Troubleshooting

### Backend can't connect to PostgreSQL
```bash
docker-compose logs postgres
docker-compose restart backend
```

### Frontend can't reach backend
- Check VITE_API_URL in docker-compose.yml
- Ensure backend is healthy: `docker-compose ps`

### Permission Issues
```bash
# On Linux/Mac
sudo chown -R $USER:$USER .
```

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d --build
```

## Useful Commands

```bash
# Rebuild services
docker-compose up -d --build

# Execute commands in containers
docker-compose exec backend python manage.py
docker-compose exec postgres psql -U postgres -d business_management

# View resource usage
docker stats

# Clean up unused resources
docker system prune -a
```
