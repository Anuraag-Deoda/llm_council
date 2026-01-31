# LLM Council

A sophisticated web application that leverages collective intelligence from multiple AI models to provide comprehensive, well-researched answers to your questions.

## Overview

Instead of asking a single LLM for an answer, the LLM Council orchestrates a multi-stage deliberation process:

1. **Stage 1: First Opinions** - Multiple LLMs independently respond to your query
2. **Stage 2: Peer Review** - Each LLM reviews and ranks the other responses (anonymized)
3. **Stage 3: Final Response** - A Chairman model (GPT-5.2) synthesizes all perspectives into a final answer

## Features

- 🤖 **Multiple AI Models**: Leverages both OpenAI models (GPT-5.2, GPT-4o) and 7 free OpenRouter models
- 🔄 **Real-time Streaming**: See responses as they're generated with live stage indicators
- 📊 **Transparent Process**: View individual model responses in an organized tab interface
- ⚖️ **Peer Review System**: Models evaluate each other's work for quality and accuracy
- 💾 **Conversation History**: Persistent storage of all conversations
- 🎛️ **Model Selection**: Choose which models participate in the council
- 🎨 **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## Architecture

### Backend (FastAPI)
- **Python 3.8+** with async/await for concurrent API calls
- **FastAPI** for high-performance REST API
- **OpenAI SDK** for GPT models
- **OpenRouter API** for free model access
- **JSON-based storage** for conversation history

### Frontend (Next.js)
- **React 18** with TypeScript
- **Next.js 14** App Router
- **Tailwind CSS** for styling
- **React Markdown** for rendering responses
- **Streaming API** for real-time updates

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- OpenAI API key (for GPT-5.2 and GPT-4o)
- OpenRouter API key (for free models)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd llm_council
```

### 2. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required environment variables in `.env`:**

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# The default API URL (http://localhost:8000) should work if backend runs locally
```

## Running the Application

### Start the Backend

```bash
cd backend
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows

# Run the FastAPI server
python -m app.main

# Or use uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Start the Frontend

In a new terminal:

```bash
cd frontend

# Run the Next.js development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Usage

1. Open your browser to `http://localhost:3000`
2. (Optional) Click "Council Members" to select which models to include
3. Type your question in the input field
4. Press Enter or click "Send"
5. Watch the 3-stage process unfold:
   - See individual model responses in tabs
   - View peer reviews and rankings
   - Read the final synthesized answer

## Council Members

### OpenAI Models
- **GPT-5.2** (Chairman) - Latest flagship model with enhanced reasoning
- **GPT-4o** - Optimized for speed and quality

### OpenRouter Free Models
- arcee-ai/trinity-large-preview:free
- upstage/solar-pro-3:free
- liquid/lfm-2.5-1.2b-thinking:free
- tngtech/deepseek-r1t2-chimera:free
- z-ai/glm-4.5-air:free
- deepseek/deepseek-r1-0528:free
- nvidia/nemotron-3-nano-30b-a3b:free

## Project Structure

```
llm_council/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── llm_service.py          # Unified LLM interface
│   │   │   ├── openai_service.py       # OpenAI API integration
│   │   │   ├── openrouter_service.py   # OpenRouter API integration
│   │   │   └── council_orchestrator.py # 3-stage orchestration logic
│   │   ├── routes/
│   │   │   ├── chat.py                 # Chat endpoints
│   │   │   └── models.py               # Model listing endpoints
│   │   ├── database/
│   │   │   └── storage.py              # JSON-based storage
│   │   ├── config.py                   # Configuration management
│   │   ├── models.py                   # Pydantic models
│   │   └── main.py                     # FastAPI application
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Home page
│   │   ├── layout.tsx                  # Root layout
│   │   └── globals.css                 # Global styles
│   ├── components/
│   │   ├── ChatInterface.tsx           # Main chat component
│   │   ├── MessageList.tsx             # Message display
│   │   ├── TabView.tsx                 # Model response tabs
│   │   ├── StageIndicator.tsx          # Stage progress indicator
│   │   └── ModelSelector.tsx           # Model selection UI
│   ├── lib/
│   │   └── api.ts                      # API client
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
└── README.md
```

## API Endpoints

### Chat Endpoints

- `POST /chat/stream` - Stream a council response (recommended)
- `POST /chat/` - Get a complete council response (non-streaming)
- `GET /chat/history/{conversation_id}` - Get conversation history
- `GET /chat/conversations` - List all conversations
- `DELETE /chat/history/{conversation_id}` - Delete a conversation

### Model Endpoints

- `GET /models/` - List all available models
- `GET /models/chairman` - Get chairman model info

## How It Works

### Stage 1: First Opinions

All selected models receive the user's query independently. Requests are made in parallel for speed. Each model provides its initial response without seeing others' answers.

### Stage 2: Peer Review

Each model reviews the responses from other models (anonymized to prevent bias). Models rank responses based on accuracy, completeness, and usefulness, providing reasoning for their rankings.

### Stage 3: Final Response

The Chairman model (GPT-5.2) receives:
- The original user query
- All first opinions from council members
- All peer reviews and rankings

It synthesizes this information into a comprehensive final answer that represents the best collective intelligence of the council.

## Configuration

### Backend Configuration (backend/.env)

```env
# API Keys
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key

# Chairman Model
CHAIRMAN_MODEL=gpt-5.2

# Application Settings
MAX_TOKENS=4000
TEMPERATURE=0.7
REQUEST_TIMEOUT=120

# Database
DATABASE_PATH=./data/conversations.json

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend Configuration (frontend/.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Change the port in the run command
uvicorn app.main:app --reload --port 8001
# Update NEXT_PUBLIC_API_URL in frontend/.env.local accordingly
```

**API Key errors:**
- Verify your API keys are correctly set in backend/.env
- Check that the .env file is in the backend directory
- Ensure no extra spaces or quotes around keys

**Module import errors:**
```bash
# Make sure you're in the backend directory and virtual environment is activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Module not found errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

**API connection errors:**
- Verify backend is running on port 8000
- Check NEXT_PUBLIC_API_URL in .env.local
- Look for CORS errors in browser console

## Development

### Adding New Models

Edit `backend/app/config.py`:

```python
# Add to openrouter_models list
openrouter_models: List[str] = [
    "your-new-model:free",
    # ... existing models
]

# Or add to openai_models list
openai_models: List[str] = [
    "new-openai-model",
    # ... existing models
]
```

### Customizing the Chairman

Edit `backend/.env`:

```env
CHAIRMAN_MODEL=gpt-4o  # or any other model
```

## Production Deployment

### Backend

1. Set `DEBUG=False` in production
2. Use a production ASGI server (uvicorn with workers)
3. Set up proper CORS origins
4. Use a real database (PostgreSQL, MongoDB)
5. Add authentication/authorization
6. Set up rate limiting

### Frontend

```bash
cd frontend
npm run build
npm start
```

Use a reverse proxy (nginx) and process manager (PM2).

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Built with ❤️ using FastAPI, Next.js, and the power of collective AI intelligence.
