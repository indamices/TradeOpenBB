# Test Runner Script
# Usage: .\run_tests.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SmartQuant Test Suite" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if backend server is running
function Test-BackendRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Start backend if not running
if (-not (Test-BackendRunning)) {
    Write-Host "Backend server is not running. Starting it..." -ForegroundColor Yellow
    
    # Check if .env exists
    if (-not (Test-Path "backend\.env")) {
        if (Test-Path "backend\.env.example") {
            Copy-Item "backend\.env.example" "backend\.env"
        } else {
            @"
DATABASE_URL=sqlite:///./test_smartquant.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
        }
    }
    
    # Initialize test database
    Set-Location backend
    python -c "from database import init_db; init_db(); print('Test database initialized')" 2>&1 | Out-Null
    Set-Location ..
    
    # Start backend in background
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PSScriptRoot
        Set-Location backend
        $env:DATABASE_URL = "sqlite:///./test_smartquant.db"
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
        if (Test-BackendRunning) {
            $ready = $true
            Write-Host "✅ Backend is ready" -ForegroundColor Green
        }
    }
    
    if (-not $ready) {
        Write-Host "❌ Backend failed to start" -ForegroundColor Red
        Receive-Job $backendJob
        Remove-Job $backendJob
        exit 1
    }
    
    $script:backendStarted = $true
} else {
    Write-Host "✅ Backend is already running" -ForegroundColor Green
    $script:backendStarted = $false
}

# Run Python tests
Write-Host "`n🧪 Running Python Tests..." -ForegroundColor Cyan
Set-Location backend

# Check if pytest is installed
python -c "import pytest" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pytest..." -ForegroundColor Yellow
    python -m pip install pytest pytest-asyncio httpx --quiet
}

# Run tests
Write-Host ""
python -m pytest tests/ -v --tb=short
$testExitCode = $LASTEXITCODE

Set-Location ..

# Cleanup
if ($script:backendStarted) {
    Write-Host "`nStopping test backend..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
if ($testExitCode -eq 0) {
    Write-Host "  ✅ All Tests Passed" -ForegroundColor Green
} else {
    Write-Host "  ❌ Some Tests Failed" -ForegroundColor Red
}
Write-Host "========================================`n" -ForegroundColor Cyan

exit $testExitCode
