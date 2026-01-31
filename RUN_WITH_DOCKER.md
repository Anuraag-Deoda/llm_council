# Run LLM Council with Docker - Quick Reference

## ✅ Your API keys are already configured in `backend/.env`

## 🚀 Start the Application

```bash
# Build and start everything
docker-compose up --build
```

Wait for:
```
backend_1   | INFO:     Application startup complete.
frontend_1  | ✓ Ready in X.Xs
```

Then open: **http://localhost:3000**

---

## 📋 Common Commands

### Start (detached/background)
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop
```bash
docker-compose down
```

### Restart
```bash
docker-compose restart
```

### Rebuild after changes
```bash
docker-compose up --build
```

### Stop and delete all data
```bash
docker-compose down -v
```

---

## 🔧 Troubleshooting

### Port already in use?
```bash
# Find and kill process on port 8000 or 3000
lsof -i :8000
kill -9 <PID>
```

### View errors?
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Clean restart?
```bash
docker-compose down -v
docker-compose up --build
```

---

## 📊 What's Running?

- **Backend**: http://localhost:8000 (API)
- **Backend Docs**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:3000 (Web App)

---

**That's it! Your LLM Council is running in Docker.** 🏛️✨

For detailed Docker guide, see [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
