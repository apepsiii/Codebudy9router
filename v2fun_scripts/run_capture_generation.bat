@echo off
REM V2Fun.ai Generation Flow Capture Launcher
REM Interactive mode to capture API calls during manual generation

echo ========================================
echo V2Fun.ai Generation Flow Capture
echo ========================================
echo.

echo [INFO] This script will:
echo   1. Load your saved session
echo   2. Open browser with authenticated session
echo   3. Show step-by-step instructions
echo   4. Capture all API calls during generation
echo.

echo [INFO] Starting capture script...
echo.

python v2fun_scripts/capture_generation_flow.py

echo.
echo ========================================
echo Capture completed!
echo Check v2fun_data/ folder for results
echo ========================================
pause
