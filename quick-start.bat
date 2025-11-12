@echo off
echo ========================================
echo   TRIBI eSIM - Quick Start
echo ========================================
echo.

REM Check if MySQL is running
echo [1/5] Checking MySQL...
mysql -u root -p1234 -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] MySQL not running or wrong password
    echo Please start MySQL and update password in apps\backend\.env
    pause
    exit /b 1
)
echo [OK] MySQL is running

REM Create database if not exists
echo.
echo [2/5] Creating database...
mysql -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS tribi_dev;" >nul 2>&1
echo [OK] Database ready

REM Backend setup
echo.
echo [3/5] Setting up backend...
cd apps\backend

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo Running migrations...
alembic upgrade head

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo Terminal 1 - Backend:
echo   cd apps\backend
echo   .venv\Scripts\activate
echo   uvicorn app.main:app --reload
echo.
echo Terminal 2 - Web Frontend:
echo   cd apps\web
echo   npm install  (first time only)
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo.
echo Admin Panel: http://localhost:3000/admin
echo   (Make sure your email is in ADMIN_EMAILS)
echo.
pause
