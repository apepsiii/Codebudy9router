@echo off
REM V2Fun Backend API Launcher
REM Quick start script for Windows

echo ================================================================
echo           V2FUN BACKEND API - LAUNCHER
echo ================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [1] Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [WARN] Flask not installed. Installing dependencies...
    pip install flask flask-cors
)

echo.
echo [2] Checking accounts...
python -c "from v2fun_scripts.database import get_db; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM v2fun_accounts WHERE status=\"done\"'); count = cursor.fetchone()[0]; print(f'Available accounts: {count}'); conn.close()" 2>nul

echo.
echo [3] Starting V2Fun Backend API...
echo     Port: 5001
echo     URL: http://localhost:5001
echo.
echo Press Ctrl+C to stop
echo.

python v2fun_backend_api.py

pause
