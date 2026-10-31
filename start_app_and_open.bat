@echo off
echo ========================================================
echo Starting ANN-DAAN AI Platform (Jaipur Pilot Node)
echo ========================================================
cd /d "%~dp0"
start "ANN-DAAN AI Backend" cmd /k "start_backend.bat"
timeout /t 3 /nobreak >nul
start "ANN-DAAN AI Frontend" cmd /k "start_frontend.bat"
timeout /t 4 /nobreak >nul
start http://localhost:3001
echo Both services started! Browser opened at http://localhost:3001
