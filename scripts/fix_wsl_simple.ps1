# Simple WSL Fix using official wsl --install command
# Usage: .\scripts\fix_wsl_simple.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Simple WSL Fix" -ForegroundColor Cyan
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

# Method 1: Try wsl --install (Windows 10 2004+ / Windows 11)
Write-Host "[1] Attempting official WSL installation method..." -ForegroundColor Yellow
Write-Host "   Running: wsl --install" -ForegroundColor Gray
Write-Host "   This will install WSL with Ubuntu by default" -ForegroundColor Gray
Write-Host ""

try {
    # Use wsl --install to install WSL completely
    # This command handles everything: features, kernel, distribution
    $result = wsl --install 2>&1 | Out-String
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ WSL installation initiated successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Output:" -ForegroundColor Gray
        Write-Host $result -ForegroundColor White
    } else {
        Write-Host "⚠️  Installation command returned exit code: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Output:" -ForegroundColor Gray
        Write-Host $result -ForegroundColor White
        Write-Host ""
        
        # If wsl --install fails, try alternative method
        Write-Host "[2] Trying alternative installation method..." -ForegroundColor Yellow
        
        # Enable required features
        Write-Host "   Enabling Windows features..." -ForegroundColor Gray
        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart -All | Out-Null
        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart -All | Out-Null
        Write-Host "   ✅ Features enabled" -ForegroundColor Green
        
        # Download and install kernel update
        Write-Host "   Downloading WSL kernel update..." -ForegroundColor Gray
        $wslUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
        $downloadPath = "$env:TEMP\wsl_update_x64.msi"
        
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $wslUpdateUrl -OutFile $downloadPath -UseBasicParsing
        
        if (Test-Path $downloadPath) {
            Write-Host "   Installing WSL kernel update..." -ForegroundColor Gray
            Start-Process msiexec.exe -ArgumentList "/i `"$downloadPath`" /quiet /norestart" -Wait -Verb RunAs -WindowStyle Hidden
            Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ Kernel update installed" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation required:" -ForegroundColor Yellow
    Write-Host "  1. Open PowerShell as Administrator" -ForegroundColor White
    Write-Host "  2. Run: wsl --install" -ForegroundColor Cyan
    Write-Host "  3. Restart computer when prompted" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Process Started" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. RESTART your computer (required!)" -ForegroundColor White
Write-Host ""
Write-Host "2. After restart, if Ubuntu was not installed automatically:" -ForegroundColor White
Write-Host "   - Open Microsoft Store" -ForegroundColor Gray
Write-Host "   - Search for 'Ubuntu'" -ForegroundColor Gray
Write-Host "   - Install 'Ubuntu 22.04 LTS'" -ForegroundColor Gray
Write-Host "   - Or run: wsl --install -d Ubuntu" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Verify WSL installation:" -ForegroundColor White
Write-Host "   wsl --version" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Restart Docker Desktop" -ForegroundColor White
Write-Host ""
Write-Host "5. Run: .\scripts\test_auto.ps1" -ForegroundColor White
Write-Host ""
