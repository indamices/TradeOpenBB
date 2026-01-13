# Start server and run tests
$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Start Server and Run Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "Creating backend\.env..." -ForegroundColor Yellow
    @"
DATABASE_URL=sqlite:///./test_smartquant.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
Set-Location backend
python -c "import sys; sys.path.insert(0, '.'); from database import init_db; init_db(); print('Database initialized')" 2>&1 | Out-Null
Set-Location ..

# Start backend
Write-Host "Starting backend server..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    Set-Location backend
    python -m uvicorn main:app --host 0.0.0.0 --port 8000
}

# Wait for backend
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
        $ready = $true
        Write-Host "✅ Backend is ready!" -ForegroundColor Green
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $ready) {
    Write-Host "`n❌ Backend failed to start" -ForegroundColor Red
    Receive-Job $backendJob
    Remove-Job $backendJob
    exit 1
}

Write-Host "`nRunning tests...`n" -ForegroundColor Cyan

# Run tests
python backend/run_tests_simple.py
$testExitCode = $LASTEXITCODE

# Cleanup
Write-Host "`nStopping backend..." -ForegroundColor Yellow
Stop-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -ErrorAction SilentlyContinue

exit $testExitCode
