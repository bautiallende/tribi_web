@echo off
REM Script para iniciar todo el entorno de desarrollo de Tribi
REM Usa PowerShell para mantener las ventanas abiertas

echo ========================================
echo   TRIBI - Starting Development Environment
echo ========================================
echo.

REM Verificar que MySQL está corriendo
echo Checking MySQL...
docker ps | findstr mysql >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MySQL is not running!
    echo Please start Docker and run: docker compose -f infrastructure/docker-compose.yml up -d
    pause
    exit /b 1
)
echo [OK] MySQL is running

echo.
echo Starting services...
echo.

REM Iniciar Backend en una nueva ventana de PowerShell
echo [1/3] Starting Backend (FastAPI)...
start "Tribi Backend" powershell -NoExit -Command "cd '%~dp0apps\backend'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  BACKEND (FastAPI) - Port 8000' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; python -m uvicorn app.main:app --reload --port 8000"

REM Esperar 3 segundos
timeout /t 3 /nobreak >nul

REM Iniciar Frontend en una nueva ventana de PowerShell
echo [2/3] Starting Frontend (Next.js)...
start "Tribi Frontend" powershell -NoExit -Command "cd '%~dp0apps\web'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  FRONTEND (Next.js) - Port 3000' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; npm run dev"

REM Esperar 2 segundos
timeout /t 2 /nobreak >nul

REM Iniciar Mobile en una nueva ventana de PowerShell
echo [3/3] Starting Mobile (Expo)...
start "Tribi Mobile" powershell -NoExit -Command "cd '%~dp0apps\mobile'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '  MOBILE (Expo)' -ForegroundColor Cyan; Write-Host '========================================' -ForegroundColor Cyan; Write-Host ''; npx expo start --clear"

echo.
echo ========================================
echo   All services are starting...
echo ========================================
echo.
echo Backend:   http://localhost:8000
echo Frontend:  http://localhost:3000
echo Mobile:    Check Expo terminal for QR code
echo.
echo To stop all services, close the PowerShell windows.
echo.
echo Wait 10-15 seconds for all services to be ready, then run:
echo   python test_auth_flow.py
echo.
pause
