# 🐳 Docker Quick Reference

## Quick Commands (Using Makefile)

```bash
# Start the app
make start

# Restart containers (quick - no rebuild)
make restart

# Rebuild and restart (after code changes)
make rebuild

# Stop the app
make stop

# View logs
make logs

# Check container status
make status

# Clean everything (remove volumes too)
make clean
```

## Docker Compose Commands (Direct)

### Starting the App

```bash
# Start all services in background
docker-compose up -d

# Start with logs visible
docker-compose up

# Start only specific services
docker-compose up -d backend frontend
```

### Restarting the App

```bash
# Quick restart (no rebuild) - Use when NO code changes
docker-compose restart

# Restart a specific service
docker-compose restart backend

# Stop and start (rebuild on start) - Use when code changed
docker-compose down && docker-compose up -d

# Full rebuild (clears cache) - Use when dependencies changed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Stopping the App

```bash
# Stop containers (keeps volumes)
docker-compose down

# Stop containers and remove volumes (database data will be lost!)
docker-compose down -v

# Stop a specific service
docker-compose stop backend
```

### Viewing Logs

```bash
# View all logs (follow mode)
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100

# View logs since timestamp
docker-compose logs --since 2024-01-01T00:00:00
```

### Container Management

```bash
# Check status of all containers
docker-compose ps

# Execute command in running container
docker-compose exec backend bash
docker-compose exec backend python manage.py migrate

# Rebuild specific service
docker-compose build backend

# Scale a service (run multiple instances)
docker-compose up -d --scale backend=3
```

### Troubleshooting

```bash
# View detailed container info
docker-compose ps -a

# Check container logs for errors
docker-compose logs backend | grep -i error

# Remove stopped containers and orphaned volumes
docker-compose down --remove-orphans

# Restart with fresh build
docker-compose down
docker-compose build --no-cache --pull
docker-compose up -d

# Check which ports are in use
docker-compose ps
netstat -an | grep "8000\|3000\|5432\|6379"

# Access backend shell
docker-compose exec backend /bin/sh

# Access database
docker-compose exec db psql -U postgres -d fda_db
```

## Common Workflows

### 1. After Pulling New Code

```bash
make rebuild
# or
docker-compose down && docker-compose build && docker-compose up -d
```

### 2. Quick Restart (No Code Changes)

```bash
make restart
# or
docker-compose restart
```

### 3. Backend Only Changes

```bash
docker-compose restart backend
# or if you updated dependencies
docker-compose build backend && docker-compose up -d
```

### 4. Frontend Only Changes

```bash
docker-compose restart frontend
# or if you updated dependencies
docker-compose build frontend && docker-compose up -d
```

### 5. Check if Everything is Running

```bash
make status
# Should show:
# - frontend (port 3000)
# - backend (port 8000)
# - db (port 5432)
# - redis (port 6379)
```

### 6. Debugging Backend Issues

```bash
# View backend logs
docker-compose logs -f backend

# Access backend container
docker-compose exec backend bash

# Check environment variables
docker-compose exec backend env | grep API_KEY

# Restart just the backend
docker-compose restart backend
```

## Environment Variables

Make sure your `.env` file exists in the project root with:

```bash
# AI Provider API Keys
GEMINI_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# DEEPSEEK_API_KEY=your_key_here

# Optional
# AI_MODEL=gemini-flash-latest
```

## Ports Reference

- **3000** - Frontend (React/Vite)
- **8000** - Backend (FastAPI)
- **5432** - PostgreSQL Database
- **6379** - Redis Cache

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/

---

💡 **Pro Tip**: Use `make help` to see all available commands!

