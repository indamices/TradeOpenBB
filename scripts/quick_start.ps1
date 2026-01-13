# Quick Start Script - Start both backend and frontend
# Usage: .\quick_start.ps1

param(
    [switch]$Test = $false,
    [switch]$BackendOnly = $false,
    [switch]$FrontendOnly = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SmartQuant Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running tests only
if ($Test) {
    Write-Host "Running tests only..." -ForegroundColor Yellow
    & "$PSScriptRoot\run_tests.ps1"
    exit $LASTEXITCODE
}

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

# Check ports
$backendPort = 8000
$frontendPort = 5173

if (Test-Port -Port $backendPort) {
    Write-Host "⚠️  Port $backendPort is already in use" -ForegroundColor Yellow
    $useExisting = Read-Host "Use existing backend? (y/n)"
    if ($useExisting -ne "y") {
        Write-Host "Please stop the service on port $backendPort and try again" -ForegroundColor Red
        exit 1
    }
    $backendRunning = $true
} else {
    $backendRunning = $false
}

if (Test-Port -Port $frontendPort) {
    Write-Host "⚠️  Port $frontendPort is already in use" -ForegroundColor Yellow
    $useExisting = Read-Host "Use existing frontend? (y/n)"
    if ($useExisting -ne "y") {
        Write-Host "Please stop the service on port $frontendPort and try again" -ForegroundColor Red
        exit 1
    }
    $frontendRunning = $true
} else {
    $frontendRunning = $false
}

# Start Backend
if (-not $FrontendOnly) {
    if (-not $backendRunning) {
        Write-Host "`n🚀 Starting Backend Server..." -ForegroundColor Green
        
        # Check Python
        if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
            exit 1
        }
        
        # Check if .env exists
        if (-not (Test-Path "backend\.env")) {
            Write-Host "Creating backend\.env from template..." -ForegroundColor Yellow
            if (Test-Path "backend\.env.example") {
                Copy-Item "backend\.env.example" "backend\.env"
            } else {
                @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
            }
        }
        
        # Initialize database
        Write-Host "Initializing database..." -ForegroundColor Yellow
        Set-Location backend
        python -c "from database import init_db; init_db(); print('✅ Database initialized')" 2>&1 | Out-Null
        Set-Location ..
        
        # Start backend in background
        Write-Host "Starting backend on http://localhost:$backendPort" -ForegroundColor Cyan
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:PSScriptRoot
            Set-Location backend
            python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        }
        
        # Wait for backend to be ready
        Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
        $maxAttempts = 30
        $attempt = 0
        $ready = $false
        
        while ($attempt -lt $maxAttempts -and -not $ready) {
            Start-Sleep -Seconds 1
            $attempt++
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$backendPort" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
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
        
        Write-Host "Backend API: http://localhost:$backendPort" -ForegroundColor Cyan
        Write-Host "API Docs:    http://localhost:$backendPort/docs`n" -ForegroundColor Cyan
    } else {
        Write-Host "✅ Using existing backend on port $backendPort" -ForegroundColor Green
    }
}

# Start Frontend
if (-not $BackendOnly) {
    if (-not $frontendRunning) {
        Write-Host "🚀 Starting Frontend Server..." -ForegroundColor Green
        
        # Check Node.js
        if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
            exit 1
        }
        
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
            npm install
        }
        
        # Start frontend in background
        Write-Host "Starting frontend on http://localhost:$frontendPort" -ForegroundColor Cyan
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:PSScriptRoot
            npm run dev
        }
        
        # Wait a bit for frontend to start
        Start-Sleep -Seconds 3
        
        Write-Host "✅ Frontend is starting!" -ForegroundColor Green
        Write-Host "Frontend: http://localhost:$frontendPort`n" -ForegroundColor Cyan
    } else {
        Write-Host "✅ Using existing frontend on port $frontendPort" -ForegroundColor Green
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Services Running" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:$backendPort" -ForegroundColor White
Write-Host "API Docs: http://localhost:$backendPort/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:$frontendPort" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep script running and show logs
try {
    if (-not $FrontendOnly -and -not $backendRunning) {
        Write-Host "Backend logs:" -ForegroundColor Cyan
        Receive-Job $backendJob -Wait
    }
    if (-not $BackendOnly -and -not $frontendRunning) {
        Write-Host "Frontend logs:" -ForegroundColor Cyan
        Receive-Job $frontendJob -Wait
    }
} catch {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    if (-not $FrontendOnly -and -not $backendRunning) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    if (-not $BackendOnly -and -not $frontendRunning) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
}
