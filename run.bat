@echo off
echo ===================================================
echo Starting RailSync Operations Suite
echo ===================================================

echo [1/2] Launching Backend AI (FastAPI :8000)...
start "RailSync Backend API" cmd /k "cd /d %~dp0backend-ai && ..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo [2/2] Launching Frontend Cockpit (Vite :5173)...
start "RailSync Frontend Cockpit" cmd /k "cd /d %~dp0frontend-cockpit && npm.cmd run dev"

echo Waiting for servers to initialize...
timeout /t 3 >nul
start http://localhost:5173

echo.
echo All services launched! You can access the cockpit at http://localhost:5173
