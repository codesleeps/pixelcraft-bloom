#!/bin/bash
# Chatbot Startup Script
# Builds and starts all Docker services with clean cache

set -e

echo "🐳 Building Docker services with --no-cache..."
docker compose build --no-cache

echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Services started! Check logs with: docker compose logs -f backend"
echo ""
echo "🧪 Test the chat API:"
echo "   cd backend && .venv/bin/python test_chat_api.py"
echo ""
echo "🌐 Start frontend:"
echo "   npm run dev"
