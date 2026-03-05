# Case-Verify AI Startup Script (PowerShell)
# This script loads environment from .env and starts the application

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Case-Verify AI - Legal Analysis System" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Load environment variables from .env file if it exists
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "[INFO] Environment loaded from .env file" -ForegroundColor Green
} else {
    Write-Host "[WARN] No .env file found. Copy .env.example to .env and configure it." -ForegroundColor Yellow
    Write-Host "[WARN] Run: Copy-Item .env.example .env" -ForegroundColor Yellow
    exit 1
}

# Validate required environment variables
if (-not $env:GEMINI_API_KEY -or $env:GEMINI_API_KEY -eq "your_gemini_api_key_here") {
    Write-Host "[ERROR] GEMINI_API_KEY is not set or still a placeholder." -ForegroundColor Red
    Write-Host "[ERROR] Edit your .env file and set a valid API key." -ForegroundColor Red
    exit 1
}

$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

Write-Host "[INFO] Environment configured" -ForegroundColor Green
Write-Host "[INFO] API Key: $($env:GEMINI_API_KEY.Substring(0,10))..." -ForegroundColor Green
Write-Host "[INFO] Starting application..." -ForegroundColor Green
Write-Host ""

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
