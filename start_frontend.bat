@echo off
title ANN-DAAN AI - Frontend Service (Next.js)
echo ===================================================================
echo Starting ANN-DAAN AI Frontend Service (Next.js 16 / React 19)
echo ===================================================================

cd /d "%~dp0frontend"

:: This project uses port 3001 so it can run alongside other local apps.
netstat -ano | findstr :3001 | findstr LISTENING >nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] A service is already listening on port 3001.
    echo Frontend is already running or port 3001 is occupied.
    echo Application: http://localhost:3001
    pause
    exit /b 0
)

set "NEXT_PUBLIC_API_URL=http://localhost:8001/api"
echo Starting Next.js development server on http://localhost:3001 ...
npm run dev -- --port 3001
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Frontend failed to start. Return code: %ERRORLEVEL%
    pause
)
