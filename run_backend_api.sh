#!/bin/bash
# V2Fun Backend API Launcher for Linux/Mac

echo "================================================================"
echo "           V2FUN BACKEND API - LAUNCHER"
echo "================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found. Please install Python first."
    exit 1
fi

echo "[1] Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[WARN] Flask not installed. Installing dependencies..."
    pip3 install flask flask-cors
fi

echo ""
echo "[2] Checking accounts..."
python3 -c "from v2fun_scripts.database import get_db; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM v2fun_accounts WHERE status=\"done\"'); count = cursor.fetchone()[0]; print(f'Available accounts: {count}'); conn.close()" 2>/dev/null

echo ""
echo "[3] Starting V2Fun Backend API..."
echo "    Port: 5001"
echo "    URL: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 v2fun_backend_api.py
