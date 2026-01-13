# Manual dependency installation script
# This script installs packages one by one to work around pip issues

Write-Host "Installing backend dependencies manually..." -ForegroundColor Green

$packages = @(
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "psycopg2-binary",
    "pydantic",
    "pandas",
    "numpy",
    "yfinance",
    "requests",
    "python-dotenv",
    "cryptography",
    "cachetools"
)

$successCount = 0
$failCount = 0

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    try {
        # Try using python -m pip first
        python -m pip install $package --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $package installed" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ✗ Failed to install $package" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ✗ Error installing $package: $_" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`nInstallation Summary:" -ForegroundColor Cyan
Write-Host "  Success: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor Red

if ($failCount -eq 0) {
    Write-Host "`nAll dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nSome packages failed to install. You may need to:" -ForegroundColor Yellow
    Write-Host "  1. Update Python to 3.11+"
    Write-Host "  2. Reinstall pip: python -m ensurepip --upgrade"
    Write-Host "  3. Install packages individually"
}
