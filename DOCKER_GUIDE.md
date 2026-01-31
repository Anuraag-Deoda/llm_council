# Docker Deployment Guide

This guide shows you how to run the LLM Council application using Docker Compose.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- Your API keys already configured in `backend/.env`

## Quick Start

### 1. Verify Your API Keys

Make sure `backend/.env` has your API keys:

```bash
cat backend/.env | grep API_KEY
```

You should see:
- `OPENAI_API_KEY=sk-...`
- `OPENROUTER_API_KEY=sk-...`

### 2. Build and Start

From the project root directory:

```bash
# Build and start both services
docker-compose up --build
```

This will:
- Build the backend Docker image
- Build the frontend Docker image
- Start both containers
- Create a persistent volume for conversation data

### 3. Wait for Services to Start

Watch the logs until you see:

```
backend_1   | INFO:     Application startup complete.
frontend_1  | ▲ Next.js 14.1.0
frontend_1  | - Local:        http://localhost:3000
frontend_1  | ✓ Ready in X.Xs
```

### 4. Access the Application

Open your browser to:
```
http://localhost:3000
```

## Docker Commands

### Start in Background (Detached Mode)

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Stop Services

```bash
# Stop and remove containers
docker-compose down

# Stop, remove containers, and delete volumes (clears conversation history)
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up --build

# Or rebuild specific service
docker-compose build backend
docker-compose build frontend
```

### Check Service Status

```bash
docker-compose ps
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are already in use:

**Option 1: Stop the conflicting service**
```bash
# Find what's using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**Option 2: Change the port in docker-compose.yml**
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change left side to different port
```

### View Container Logs

```bash
# Real-time logs
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Access Container Shell

```bash
# Backend container
docker-compose exec backend bash

# Frontend container
docker-compose exec frontend sh
```

### Clear Everything and Start Fresh

```bash
# Stop and remove everything
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose up --build
```

### Check Environment Variables

```bash
# View backend environment
docker-compose exec backend env | grep API_KEY
```

## File Structure for Docker

```
llm_council/
├── docker-compose.yml           # Orchestration file
├── backend/
│   ├── Dockerfile               # Backend container definition
│   ├── .env                     # Your API keys (used by Docker)
│   └── app/                     # Application code
└── frontend/
    ├── Dockerfile               # Frontend container definition
    └── ...                      # Application code
```

## Persistent Data

Conversation data is stored in a Docker volume named `backend-data`.

**View volume:**
```bash
docker volume ls | grep backend-data
```

**Inspect volume:**
```bash
docker volume inspect llm_council_backend-data
```

**Backup conversations:**
```bash
docker-compose exec backend cat /app/data/conversations.json > backup.json
```

**Restore conversations:**
```bash
docker-compose exec backend sh -c 'cat > /app/data/conversations.json' < backup.json
```

## Production Deployment

For production, consider:

### 1. Use Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    environment:
      - DATABASE_PATH=/app/data/conversations.json
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - backend-data:/app/data
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  backend-data:
```

### 2. Add Health Checks

Update docker-compose.yml:

```yaml
services:
  backend:
    # ... existing config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 3. Resource Limits

```yaml
services:
  backend:
    # ... existing config
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Common Issues

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

### Issue: "Port is already allocated"

**Solution:**
```bash
# Stop all containers
docker-compose down

# Check what's using the port
lsof -i :8000
lsof -i :3000
```

### Issue: "Build failed"

**Solution:**
```bash
# Clean build cache
docker builder prune

# Rebuild without cache
docker-compose build --no-cache
```

### Issue: Frontend can't reach backend

**Solution:**
Check that CORS_ORIGINS includes your frontend URL:
```bash
# In backend/.env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Monitoring

### View Resource Usage

```bash
docker stats
```

### View Container Details

```bash
docker-compose ps
docker inspect llm_council_backend_1
```

## Updating the Application

When you make code changes:

```bash
# For backend changes
docker-compose up --build backend

# For frontend changes
docker-compose up --build frontend

# For both
docker-compose up --build
```

## Stopping the Application

```bash
# Graceful shutdown
docker-compose down

# Force stop
docker-compose kill

# Stop and remove volumes (deletes data)
docker-compose down -v
```

## Next Steps

Once running:
1. Open http://localhost:3000
2. Select council members
3. Ask a question
4. Watch the 3-stage process

For detailed usage, see [README.md](README.md)

---

**Need help?** Check the troubleshooting section or view logs with `docker-compose logs -f`
