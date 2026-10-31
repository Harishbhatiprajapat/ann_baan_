@echo off
title ANN-DAAN AI - Backend Service (FastAPI)
echo ===================================================================
echo Starting ANN-DAAN AI FastAPI Backend Service (Jaipur Regional Node)
echo ===================================================================

cd /d "%~dp0"

:: Keep this project's API separate from other local development servers.
netstat -ano | findstr :8001 | findstr LISTENING >nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] A service is already listening on port 8001.
    echo Backend is already running or port 8001 is occupied.
    echo Interactive Docs: http://localhost:8001/docs
    pause
    exit /b 0
)

echo Starting uvicorn on http://localhost:8001 ...
python run_backend.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend failed to start. Return code: %ERRORLEVEL%
    pause
)
