@echo off
REM Case-Verify AI Startup Script
REM This script permanently configures the environment and starts the application

echo ===================================
echo Case-Verify AI - Legal Analysis System
echo ===================================
echo.

REM Set environment variables
set GEMINI_API_KEY=AIzaSyDDFsLnVJvV5O6hJS1hnnWz3MwmAF8sdWM
set ENVIRONMENT=development
set DEBUG=true

echo [INFO] Environment configured
echo [INFO] API Key: %GEMINI_API_KEY:~0,10%...
echo [INFO] Starting application...
echo.

REM Start the Streamlit application
python -m streamlit run app.py --server.port 8520 --server.headless false

pause
