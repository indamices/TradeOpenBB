# PowerShell script to install/update WSL
# Usage: .\scripts\install_wsl.ps1
# Note: Requires administrator privileges

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Install/Update Windows Subsystem for Linux (WSL)" -ForegroundColor Cyan
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

# Step 1: Enable WSL feature (if not already enabled)
Write-Host "[1] Checking WSL feature..." -ForegroundColor Yellow
$wslEnabled = (Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux).State -eq "Enabled"

if (-not $wslEnabled) {
    Write-Host "Enabling WSL feature..." -ForegroundColor Yellow
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
    Write-Host "✅ WSL feature enabled" -ForegroundColor Green
} else {
    Write-Host "✅ WSL feature is already enabled" -ForegroundColor Green
}

Write-Host ""

# Step 2: Enable Virtual Machine Platform (required for WSL 2)
Write-Host "[2] Checking Virtual Machine Platform..." -ForegroundColor Yellow
$vmPlatformEnabled = (Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State -eq "Enabled"

if (-not $vmPlatformEnabled) {
    Write-Host "Enabling Virtual Machine Platform..." -ForegroundColor Yellow
    Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
    Write-Host "✅ Virtual Machine Platform enabled" -ForegroundColor Green
    Write-Host "⚠️  System restart may be required" -ForegroundColor Yellow
} else {
    Write-Host "✅ Virtual Machine Platform is already enabled" -ForegroundColor Green
}

Write-Host ""

# Step 3: Install/Update WSL
Write-Host "[3] Installing/Updating WSL..." -ForegroundColor Yellow
Write-Host "This may take several minutes, please wait...`n" -ForegroundColor Gray

try {
    # Try using wsl --install (Windows 11 / latest Windows 10)
    Write-Host "Attempting to update WSL using 'wsl --update'..." -ForegroundColor Gray
    
    $wslUpdateOutput = wsl --update 2>&1
    $wslUpdateExitCode = $LASTEXITCODE
    
    if ($wslUpdateExitCode -eq 0) {
        Write-Host "✅ WSL updated successfully!" -ForegroundColor Green
        Write-Host ""
        $wslUpdateOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "⚠️  'wsl --update' failed, trying alternative method..." -ForegroundColor Yellow
        Write-Host ""
        
        # Alternative: Install via winget (Windows Package Manager)
        Write-Host "Attempting to install WSL via winget..." -ForegroundColor Gray
        $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
        
        if ($wingetCheck) {
            Write-Host "Installing WSL via winget..." -ForegroundColor Gray
            winget install --id Microsoft.WindowsSubsystemLinux --source msstore --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ WSL installed via winget" -ForegroundColor Green
            } else {
                Write-Host "⚠️  winget installation may have failed" -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  winget is not available" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ Error during WSL installation: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try:" -ForegroundColor Yellow
    Write-Host "  1. Restart your computer" -ForegroundColor White
    Write-Host "  2. Run this script again" -ForegroundColor White
    Write-Host "  3. Or manually install WSL from Microsoft Store" -ForegroundColor White
}

Write-Host ""

# Step 4: Check WSL version
Write-Host "[4] Checking WSL version..." -ForegroundColor Yellow
try {
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "WSL Version:" -ForegroundColor Gray
        $wslVersion | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "⚠️  Could not get WSL version" -ForegroundColor Yellow
        Write-Host "   WSL may need a system restart to complete installation" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not check WSL version" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Check WSL status
Write-Host "[5] Checking WSL status..." -ForegroundColor Yellow
try {
    $wslStatus = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "WSL Status:" -ForegroundColor Gray
        $wslStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    }
} catch {
    Write-Host "⚠️  Could not get WSL status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Summary and next steps
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If Virtual Machine Platform was just enabled, RESTART your computer" -ForegroundColor White
Write-Host "  2. After restart, restart Docker Desktop" -ForegroundColor White
Write-Host "  3. Run: .\scripts\test_auto.ps1" -ForegroundColor White
Write-Host ""

if (-not $vmPlatformEnabled) {
    Write-Host "⚠️  IMPORTANT: System restart is required!" -ForegroundColor Red
    Write-Host "   Please restart your computer and then restart Docker Desktop." -ForegroundColor Yellow
}
