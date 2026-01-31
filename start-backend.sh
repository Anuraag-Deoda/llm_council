#!/bin/bash

# Start script for LLM Council backend

echo "🚀 Starting LLM Council Backend..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "🔑 Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - OPENROUTER_API_KEY"
    echo ""
    read -p "Press Enter after adding your API keys..."
fi

# Start the server
echo "✨ Starting FastAPI server on http://localhost:8000"
echo ""
python -m app.main
