@echo off
echo Starting Lost & Found Intelligence...

echo Starting Backend...
start cmd /k "cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload"

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both servers are starting up in separate windows!
echo Once they are ready, you can open your browser to:
echo http://localhost:5173
