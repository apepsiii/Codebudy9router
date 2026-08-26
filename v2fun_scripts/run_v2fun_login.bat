@echo off
REM V2Fun.ai Google Login Automation Launcher
REM Runs the automated login script to capture JWT tokens

echo ========================================
echo V2Fun.ai Multi-Account Login Automation
echo ========================================
echo.

REM Check if account.txt file exists
if not exist "account.txt" (
    echo [ERROR] account.txt file not found!
    echo.
    echo Please create account.txt with your Google accounts:
    echo   email1@gmail.com^|password1
    echo   email2@gmail.com^|password2
    echo.
    echo You can copy account.txt.example to account.txt and edit it.
    pause
    exit /b 1
)

echo [INFO] Starting multi-account login automation...
echo [INFO] This will open a browser window
echo.

REM Run the Python script
python v2fun_scripts/v2fun_google_login.py

echo.
echo ========================================
echo Script completed!
echo Check v2fun_data/ folder for tokens
echo ========================================
pause
