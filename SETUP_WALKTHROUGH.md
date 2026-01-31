# Setup Walkthrough - First Time Users

This guide walks you through setting up and running the LLM Council application for the first time.

## Prerequisites Check

Before starting, verify you have:

```bash
# Check Python version (need 3.8+)
python3 --version

# Check Node.js version (need 18+)
node --version

# Check if ports are available
lsof -i :8000  # Should return nothing (port available)
lsof -i :3000  # Should return nothing (port available)
```

## Step-by-Step Setup

### Step 1: Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Save it securely

#### OpenRouter API Key
1. Go to https://openrouter.ai/keys
2. Sign up or log in
3. Click "Create Key"
4. Copy the key (starts with `sk-`)
5. Save it securely

### Step 2: Choose Your Setup Method

#### Option A: Docker Setup (Easiest)

**Step 2A.1: Install Docker**
- macOS: Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Linux: `sudo apt-get install docker-compose` or equivalent
- Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop

**Step 2A.2: Configure Environment**
```bash
# Navigate to project directory
cd llm_council

# Copy environment template
cp .env.docker.example .env.docker

# Edit the file
nano .env.docker  # or use your preferred editor

# Add your API keys:
OPENAI_API_KEY=sk-your-openai-key-here
OPENROUTER_API_KEY=sk-your-openrouter-key-here
```

**Step 2A.3: Start Everything**
```bash
# Build and start both services
docker-compose --env-file .env.docker up --build

# Wait for:
# ✓ backend_1  | INFO:     Application startup complete.
# ✓ frontend_1 | Ready - started server on 0.0.0.0:3000
```

**Step 2A.4: Open Browser**
```bash
# Open your browser to:
http://localhost:3000
```

#### Option B: Manual Setup

**Step 2B.1: Setup Backend**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor

# Add:
OPENAI_API_KEY=sk-your-openai-key-here
OPENROUTER_API_KEY=sk-your-openrouter-key-here
```

**Step 2B.2: Start Backend**
```bash
# Still in backend directory with venv activated
python -m app.main

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

**Step 2B.3: Setup Frontend (New Terminal)**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# The default settings should work:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Step 2B.4: Start Frontend**
```bash
# Still in frontend directory
npm run dev

# You should see:
# ▲ Next.js 14.1.0
# - Local:        http://localhost:3000
# ✓ Ready in X.Xs
```

**Step 2B.5: Open Browser**
```bash
# Open your browser to:
http://localhost:3000
```

### Step 3: First Use

**3.1: Check the Interface**
- You should see "LLM Council" header
- Input box at the bottom
- "Council Members" button at the top

**3.2: (Optional) Configure Models**
- Click "Council Members" button
- See all available models (should show 9 total)
- All models selected by default
- You can deselect models you don't want to include

**3.3: Ask Your First Question**

Try this example:
```
What are the key differences between SQL and NoSQL databases?
```

**3.4: Watch the Process**

You'll see three stages:

**Stage 1: First Opinions (10-30 seconds)**
- Progress indicator shows "First Opinions"
- Individual tabs appear for each model
- Click tabs to see different responses
- All models respond in parallel

**Stage 2: Peer Review (5-15 seconds)**
- Progress indicator shows "Peer Review"
- Models review each other's responses
- Rankings appear below tabs
- See which models ranked highest

**Stage 3: Final Response (10-20 seconds)**
- Progress indicator shows "Final Response"
- Chairman (GPT-5.2) synthesizes everything
- Final answer appears with special styling
- Gets added to conversation history

### Step 4: Verify Everything Works

**4.1: Check Backend API**
```bash
# In a new terminal:
curl http://localhost:8000/health

# Should return:
{"status":"healthy"}
```

**4.2: View API Documentation**
```bash
# Open in browser:
http://localhost:8000/docs

# You should see interactive Swagger UI with:
# - /chat/stream endpoint
# - /chat/ endpoint
# - /models/ endpoint
# - etc.
```

**4.3: Test Model Listing**
```bash
curl http://localhost:8000/models/

# Should return JSON array of 9 models
```

## Common Issues & Solutions

### Issue: "Port already in use"

**Backend (port 8000):**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change the port
uvicorn app.main:app --port 8001
# Then update frontend/.env.local to use port 8001
```

**Frontend (port 3000):**
```bash
# Find what's using the port
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or change the port
npm run dev -- -p 3001
```

### Issue: "API Key Error"

**Check your keys:**
```bash
# Backend
cd backend
cat .env | grep API_KEY

# Should show your keys (not empty)
```

**Verify key format:**
- OpenAI keys start with `sk-`
- OpenRouter keys start with `sk-`
- No quotes around keys in .env
- No extra spaces

### Issue: "Module not found"

**Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Can't connect to backend"

**Check backend is running:**
```bash
curl http://localhost:8000/health
```

**Check frontend API URL:**
```bash
cat frontend/.env.local

# Should be:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Check browser console:**
- Open Developer Tools (F12)
- Look for CORS errors
- Look for network errors

### Issue: "CORS Error"

**Update backend CORS settings:**
```bash
# Edit backend/.env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Restart backend
```

### Issue: "Docker won't start"

**Check Docker is running:**
```bash
docker --version
docker-compose --version
```

**Check environment file:**
```bash
cat .env.docker

# Should have both API keys set
```

**View logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

## Testing Your Setup

### Test 1: Simple Query
Ask: "What is 2+2?"
- All models should respond quickly
- Final answer should be correct

### Test 2: Complex Query
Ask: "Explain quantum entanglement in simple terms"
- Models will take longer
- You'll see diverse perspectives
- Final synthesis should be comprehensive

### Test 3: Model Selection
1. Click "Council Members"
2. Deselect all but 2-3 models
3. Ask a question
4. Should only see responses from selected models

### Test 4: Conversation History
1. Ask multiple questions
2. Scroll up to see previous messages
3. Click "New Conversation"
4. Previous messages should clear

## Performance Expectations

**Typical Response Times:**
- Stage 1: 15-30 seconds (depends on model speeds)
- Stage 2: 5-15 seconds
- Stage 3: 10-20 seconds
- **Total:** 30-60 seconds per query

**Note:** Free models may be slower than paid models due to rate limits.

## Next Steps

Now that everything is working:

1. **Read the full documentation:** See README.md
2. **Explore the code:** See CONTRIBUTING.md
3. **Try different questions:** Test the council's capabilities
4. **Customize:** Add/remove models, change the chairman
5. **Deploy:** Use Docker for production deployment

## Getting Help

If you're still having issues:

1. Check the logs:
   - Backend: Look at terminal output
   - Frontend: Check browser console (F12)
   - Docker: `docker-compose logs`

2. Verify your setup:
   - API keys are valid
   - Ports are available
   - Dependencies are installed

3. Review documentation:
   - README.md for detailed info
   - TROUBLESHOOTING section
   - API docs at http://localhost:8000/docs

4. Common fixes:
   - Restart both services
   - Clear browser cache
   - Check API key billing/limits
   - Verify internet connection

## Success!

If you can:
- ✅ See the chat interface
- ✅ Ask a question
- ✅ See individual model responses in tabs
- ✅ See the final synthesized answer

**Congratulations! Your LLM Council is fully operational! 🏛️✨**

Enjoy exploring the collective intelligence of multiple AI models working together!
