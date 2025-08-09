# Case-Verify AI Startup Script (PowerShell)
# This script permanently configures the environment and starts the application

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Case-Verify AI - Legal Analysis System" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables permanently for this session
$env:GEMINI_API_KEY = "AIzaSyDDFsLnVJvV5O6hJS1hnnWz3MwmAF8sdWM"
$env:ENVIRONMENT = "development"
$env:DEBUG = "true"

Write-Host "[INFO] Environment configured" -ForegroundColor Green
Write-Host "[INFO] API Key: $($env:GEMINI_API_KEY.Substring(0,10))..." -ForegroundColor Green
Write-Host "[INFO] Starting application..." -ForegroundColor Green
Write-Host ""

# Change to the application directory
Set-Location "d:\case-verify-ai"

try {
    # Start the Streamlit application
    python -m streamlit run app.py --server.port 8520 --server.headless false
}
catch {
    Write-Host "[ERROR] Failed to start application: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "Application stopped. Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
