#!/bin/bash
echo "🏆 SEKTA GOLD CUP - Ultimate Chatbot Launcher"
echo ""
echo "⚠️  SECURITY: Have you revoked leaked key at https://platform.openai.com/api-keys ?"
echo ""

if [ ! -f .env ]; then
  echo "📝 Creating .env from .env.example..."
  cp .env.example .env
  echo "❗ Edit .env and add your NEW OpenAI key, then re-run ./run.sh"
  echo "   nano .env"
  exit 1
fi

# Check if key looks compromised
if grep -q "4R35dzYfeSafQbROrcX1arD" .env; then
  echo "🚨 CRITICAL: You are still using the LEAKED key from chat!"
  echo "   Revoke it at https://platform.openai.com/api-keys NOW"
  echo "   Then put NEW key in .env"
  exit 1
fi

if grep -q "YOUR_NEW_KEY" .env; then
  echo "❗ Please set real OPENAI_API_KEY in .env"
  echo "   nano .env"
  exit 1
fi

echo "✅ Env OK"

echo ""
echo "Starting backend..."
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo "🚀 Backend at http://localhost:8000 (docs at /docs)"
python main.py &
BACKEND_PID=$!
cd ..

echo ""
echo "Starting frontend in 3s..."
sleep 3
cd frontend
if [ ! -d node_modules ]; then
  npm install
fi
echo "🎨 Frontend at http://localhost:5173"
npm run dev

kill $BACKEND_PID
