#!/bin/bash

# Start script for LLM Council frontend

echo "🚀 Starting LLM Council Frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local from template..."
    cp .env.local.example .env.local
fi

# Start the development server
echo "✨ Starting Next.js development server on http://localhost:3000"
echo ""
npm run dev
