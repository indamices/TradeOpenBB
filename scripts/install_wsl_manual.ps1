# Manual WSL Installation Script
# Downloads and installs WSL update package
# Usage: .\scripts\install_wsl_manual.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Manual WSL Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# WSL Update Package URL
$wslUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$downloadPath = "$env:TEMP\wsl_update_x64.msi"

Write-Host "[1] Downloading WSL Update Package..." -ForegroundColor Yellow
Write-Host "   URL: $wslUpdateUrl" -ForegroundColor Gray
Write-Host "   Save to: $downloadPath" -ForegroundColor Gray
Write-Host ""

try {
    # Download the WSL update package
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $wslUpdateUrl -OutFile $downloadPath -UseBasicParsing
    
    if (Test-Path $downloadPath) {
        $fileSize = (Get-Item $downloadPath).Length / 1MB
        Write-Host "✅ Download completed! ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "[2] Installing WSL Update Package..." -ForegroundColor Yellow
        Write-Host "   This will open an installer window..." -ForegroundColor Gray
        Write-Host "   Please follow the installation wizard." -ForegroundColor Gray
        Write-Host ""
        
        # Install the MSI package
        Start-Process msiexec.exe -ArgumentList "/i `"$downloadPath`" /quiet /norestart" -Wait -Verb RunAs
        
        Write-Host "✅ Installation completed!" -ForegroundColor Green
        Write-Host ""
        
        # Clean up
        Write-Host "[3] Cleaning up..." -ForegroundColor Yellow
        Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Temporary files removed" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "[4] Verifying installation..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        
        try {
            $wslVersion = wsl --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ WSL installed successfully!" -ForegroundColor Green
                Write-Host ""
                Write-Host "WSL Version:" -ForegroundColor Gray
                $wslVersion | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            } else {
                Write-Host "⚠️  Installation completed, but version check failed" -ForegroundColor Yellow
                Write-Host "   This may require a system restart" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Could not verify WSL version" -ForegroundColor Yellow
            Write-Host "   Installation may require a system restart to complete" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "❌ Download failed!" -ForegroundColor Red
        Write-Host "   Please check your internet connection" -ForegroundColor Yellow
        exit 1
    }
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation steps:" -ForegroundColor Yellow
    Write-Host "  1. Open this URL in your browser:" -ForegroundColor White
    Write-Host "     $wslUpdateUrl" -ForegroundColor Cyan
    Write-Host "  2. Download the .msi file" -ForegroundColor White
    Write-Host "  3. Right-click the .msi file and select 'Install'" -ForegroundColor White
    Write-Host "  4. Follow the installation wizard" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If prompted, RESTART your computer" -ForegroundColor White
Write-Host "  2. After restart, verify WSL: wsl --version" -ForegroundColor White
Write-Host "  3. Restart Docker Desktop" -ForegroundColor White
Write-Host "  4. Run: .\scripts\test_auto.ps1" -ForegroundColor White
Write-Host ""
