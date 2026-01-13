# PowerShell script to start all services with Docker

Write-Host "Starting SmartQuant with Docker..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "`nDocker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "`nAfter installation, restart your computer and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "`nDocker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Docker is ready. Building and starting services..." -ForegroundColor Green
Write-Host ""

# Build and start services
docker-compose up --build -d

Write-Host ""
Write-Host "Services are starting..." -ForegroundColor Yellow
Write-Host "Waiting for backend to be ready..." -ForegroundColor Yellow

# Wait for backend to be ready
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $ready = $true
        Write-Host "✅ Backend is ready!" -ForegroundColor Green
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $ready) {
    Write-Host ""
    Write-Host "⚠️  Backend is taking longer than expected to start." -ForegroundColor Yellow
    Write-Host "Check logs with: docker-compose logs backend" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Services are running!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Frontend:    Run 'npm run dev' in a new terminal" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "To stop:      docker-compose down" -ForegroundColor Yellow
}
