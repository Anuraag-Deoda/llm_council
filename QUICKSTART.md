# Quick Start Guide

Get LLM Council up and running in 5 minutes!

## Prerequisites

- Python 3.8+ and Node.js 18+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

## Option 1: Using Docker (Recommended)

### 1. Setup Environment

```bash
# Copy the docker environment template
cp .env.docker.example .env.docker

# Edit and add your API keys
nano .env.docker
```

### 2. Start Everything

```bash
# Build and start both backend and frontend
docker-compose --env-file .env.docker up --build
```

### 3. Open Your Browser

Navigate to `http://localhost:3000` and start asking questions!

## Option 2: Manual Setup

### 1. Setup Backend

```bash
# Make the startup script executable (macOS/Linux)
chmod +x start-backend.sh

# Run the startup script
./start-backend.sh
```

The script will:
- Create a virtual environment
- Install dependencies
- Create `.env` file if needed
- Start the backend server

**Add your API keys to `backend/.env`:**

```env
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
```

### 2. Setup Frontend

In a **new terminal**:

```bash
# Make the startup script executable (macOS/Linux)
chmod +x start-frontend.sh

# Run the startup script
./start-frontend.sh
```

### 3. Open Your Browser

Navigate to `http://localhost:3000` and you're ready to go!

## Using the Application

1. **Select Council Members** (Optional)
   - Click the "Council Members" button at the top
   - Check/uncheck models to include in the discussion
   - By default, all models are selected

2. **Ask a Question**
   - Type your question in the input box
   - Press Enter or click "Send"

3. **Watch the Process**
   - **Stage 1**: See each model's response in tabs
   - **Stage 2**: View peer reviews and rankings
   - **Stage 3**: Read the chairman's final synthesis

## Example Questions

Try asking:

- "Explain quantum computing in simple terms"
- "What are the pros and cons of different database types?"
- "How does blockchain technology work?"
- "What's the best way to learn a new programming language?"

## Troubleshooting

### Backend won't start

**Check Python version:**
```bash
python3 --version  # Should be 3.8 or higher
```

**Check API keys in backend/.env:**
```bash
cat backend/.env
```

### Frontend won't start

**Check Node.js version:**
```bash
node --version  # Should be 18 or higher
```

**Clear cache and reinstall:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### Can't connect to backend

**Verify backend is running:**
```bash
curl http://localhost:8000/health
```

**Check frontend API URL:**
```bash
cat frontend/.env.local
# Should contain: NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the API docs at `http://localhost:8000/docs`
- Customize the chairman model in `backend/.env`
- Add more models to the council in `backend/app/config.py`

## Getting Help

If you run into issues:

1. Check the terminal logs for error messages
2. Verify your API keys are valid
3. Make sure ports 3000 and 8000 are not in use
4. Review the troubleshooting section in README.md

Enjoy using LLM Council! 🏛️✨
