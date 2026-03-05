@echo off
REM Case-Verify AI Startup Script
REM This script loads environment from .env and starts the application

echo ===================================
echo Case-Verify AI - Legal Analysis System
echo ===================================
echo.

REM Load environment variables from .env file
if exist "%~dp0.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do (
        REM Skip comments and empty lines
        echo %%a | findstr /r "^#" >nul 2>&1
        if errorlevel 1 (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
    echo [INFO] Environment loaded from .env file
) else (
    echo [ERROR] No .env file found. Copy .env.example to .env and configure it.
    echo [ERROR] Run: copy .env.example .env
    pause
    exit /b 1
)

REM Validate required environment variables
if "%GEMINI_API_KEY%"=="" (
    echo [ERROR] GEMINI_API_KEY is not set. Edit your .env file.
    pause
    exit /b 1
)
if "%GEMINI_API_KEY%"=="your_gemini_api_key_here" (
    echo [ERROR] GEMINI_API_KEY is still a placeholder. Set a valid API key in .env
    pause
    exit /b 1
)

set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo [INFO] Environment configured
echo [INFO] API Key: %GEMINI_API_KEY:~0,10%...
echo [INFO] Starting application...
echo.

REM Start the Streamlit application
python -m streamlit run app.py --server.port 8520 --server.headless false

pause
