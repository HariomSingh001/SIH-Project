@echo off
echo ========================================================
echo   Starting Pramaan AI (Backend + Frontend)
echo ========================================================

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Pramaan AI Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting React Vite Frontend on http://127.0.0.1:5173 ...
start "Pramaan AI Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 3 /nobreak >nul

echo ========================================================
echo   Both Servers Started Successfully!
echo   Opening Dashboard in your default browser...
echo ========================================================
start http://127.0.0.1:5173

pause
