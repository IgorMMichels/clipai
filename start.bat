@echo off
REM ClipAI Startup Script for Windows

echo ========================================
echo ClipAI Startup Script
echo ========================================
echo.

echo Starting Backend Server...
cd backend
start "ClipAI Backend" cmd /k "python main.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend Server...
cd ..\frontend
start "ClipAI Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo ClipAI is ready!
echo ========================================
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window
pause >nul
