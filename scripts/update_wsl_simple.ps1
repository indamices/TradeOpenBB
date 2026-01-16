# Simple WSL Update Script
# Run this with administrator privileges

Write-Host "Updating WSL..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

try {
    $output = wsl --update 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "WSL update completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host $output
    } else {
        Write-Host "WSL update failed with exit code: $exitCode" -ForegroundColor Red
        Write-Host ""
        Write-Host "Output:" -ForegroundColor Yellow
        Write-Host $output
        Write-Host ""
        Write-Host "Please try running this script as Administrator" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error updating WSL: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking WSL version..." -ForegroundColor Cyan
wsl --version 2>&1

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Docker Desktop" -ForegroundColor White
Write-Host "2. Run: .\scripts\test_auto.ps1" -ForegroundColor White
