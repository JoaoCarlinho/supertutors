# SuperTutors Docker Setup

Complete Docker containerization for SuperTutors platform with all services.

## Services

- **Frontend** (React + Vite): `http://localhost:5173`
- **Backend** (Flask API): `http://localhost:5000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Service-Specific Commands

```bash
# Backend only
docker-compose up backend

# Frontend only
docker-compose up frontend

# Database only
docker-compose up postgres redis
```

## Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U supertutors -d supertutors_dev

# Run migrations (when implemented)
docker-compose exec backend alembic upgrade head
```

## Development Workflow

```bash
# Rebuild after code changes
docker-compose up --build

# Rebuild specific service
docker-compose up --build backend

# View service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Environment Variables

Edit `docker-compose.yml` to modify:
- Database credentials
- API URLs
- CORS origins
- Secret keys

## Health Checks

- Backend health: `curl http://localhost:5000/api/health`
- Frontend: `curl http://localhost:5173`
- PostgreSQL: `docker-compose exec postgres pg_isready -U supertutors`
- Redis: `docker-compose exec redis redis-cli ping`

## Troubleshooting

```bash
# Check service status
docker-compose ps

# Restart a service
docker-compose restart backend

# View container logs
docker-compose logs backend

# Clean build (removes all cached layers)
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v
```

## Production Notes

- Change `SECRET_KEY` and database passwords
- Use production WSGI server (gunicorn)
- Enable SSL/TLS
- Configure proper CORS origins
- Set up volume backups for postgres_data
