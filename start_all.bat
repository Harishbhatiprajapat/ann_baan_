@echo off
title ANN-DAAN AI - Master Platform Launcher
echo ===================================================================
echo ANN-DAAN AI: Food Rescue, Safety & Redistribution Platform
echo Launching Backend (FastAPI :8001) and Frontend (Next.js :3001)...
echo ===================================================================

cd /d "%~dp0"

start "ANN-DAAN Backend" cmd /k "start_backend.bat"
timeout /t 3 /nobreak >nul
start "ANN-DAAN Frontend" cmd /k "start_frontend.bat"

echo.
echo ===================================================================
echo Platform servers launched:
echo - Frontend Application: http://localhost:3001
echo - Backend Swagger Docs: http://localhost:8001/docs
echo - Backend ReDoc:        http://localhost:8001/redoc
echo ===================================================================
