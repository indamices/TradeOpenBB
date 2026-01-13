# PowerShell script to start backend locally with SQLite

Write-Host "Starting SmartQuant Backend (Local with SQLite)..." -ForegroundColor Green

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "backend\venv") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "backend\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

# Change to backend directory
Set-Location backend

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file. Please configure it if needed." -ForegroundColor Green
    } else {
        Write-Host "Creating default .env file..." -ForegroundColor Yellow
        @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=
"@ | Out-File -FilePath ".env" -Encoding utf8
    }
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -c "from database import init_db; init_db(); print('Database initialized')" 2>&1

# Start backend server
Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Green
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
