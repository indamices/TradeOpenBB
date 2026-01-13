# PowerShell script to start the frontend server

Write-Host "Starting SmartQuant Frontend Server..." -ForegroundColor Green

# Check if .env.local file exists
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local file..." -ForegroundColor Yellow
    @"
VITE_API_BASE_URL=http://localhost:8000
"@ | Out-File -FilePath ".env.local" -Encoding utf8
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Start the dev server
Write-Host "Starting Vite dev server on http://localhost:5173" -ForegroundColor Green
npm run dev
