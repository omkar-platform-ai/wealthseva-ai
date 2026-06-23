#!/bin/bash
# WealthSeva AI — One-command setup
# Run this after cloning the repo: bash scripts/setup.sh

set -e
echo "🚀 Setting up WealthSeva AI..."

# Check dependencies
command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.12+ required"; exit 1; }

# Copy env files
if [ ! -f .env ]; then cp .env.example .env; echo "✅ Created .env — fill in your API keys"; fi
if [ ! -f frontend/.env.local ]; then cp .env.example frontend/.env.local; echo "✅ Created frontend/.env.local"; fi

# Backend setup
echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
cd ..

# Frontend setup
echo "📦 Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Terminal 1 (backend):  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "  Terminal 2 (frontend): cd frontend && npm run dev"
echo ""
echo "Then open: http://localhost:3000"
