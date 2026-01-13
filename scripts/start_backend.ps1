# PowerShell script to start the backend server

Write-Host "Starting SmartQuant Backend Server..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "Warning: backend\.env file not found. Creating default..." -ForegroundColor Yellow
    @"
DATABASE_URL=postgresql://quant_user:quant_password@localhost:5432/smartquant_db
ENCRYPTION_KEY=
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
}

# Change to backend directory
Set-Location backend

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Green
pip install -q fastapi uvicorn sqlalchemy psycopg2-binary pydantic pandas numpy yfinance requests python-dotenv cryptography cachetools

# Start the server
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
uvicorn main:app --reload --host 0.0.0.0 --port 8000
