# Complete WSL Fix Script
# This script attempts to completely fix WSL installation issues
# Usage: .\scripts\fix_wsl_complete.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Complete WSL Fix" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires Administrator privileges" -ForegroundColor Yellow
    Write-Host "   Please run PowerShell as Administrator and try again" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Right-click PowerShell → Run as Administrator" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Step 1: Enable Windows features
Write-Host "[1/6] Enabling Windows features..." -ForegroundColor Cyan
$features = @(
    "Microsoft-Windows-Subsystem-Linux",
    "VirtualMachinePlatform"
)

foreach ($feature in $features) {
    Write-Host "   Checking: $feature" -ForegroundColor Gray
    try {
        $featureInfo = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
        if ($featureInfo -and $featureInfo.State -eq "Enabled") {
            Write-Host "   ✅ $feature is already enabled" -ForegroundColor Green
        } else {
            Write-Host "   Enabling: $feature..." -ForegroundColor Yellow
            Enable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart -ErrorAction Stop
            Write-Host "   ✅ Enabled: $feature" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⚠️  Could not enable $feature : $_" -ForegroundColor Yellow
    }
}
Write-Host ""

# Step 2: Download and install WSL kernel update
Write-Host "[2/6] Installing WSL kernel update..." -ForegroundColor Cyan
$kernelUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$kernelUpdatePath = "$env:TEMP\wsl_update_x64.msi"

try {
    Write-Host "   Downloading WSL kernel update..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $kernelUpdateUrl -OutFile $kernelUpdatePath -ErrorAction Stop
    Write-Host "   ✅ Downloaded to: $kernelUpdatePath" -ForegroundColor Green
    
    Write-Host "   Installing kernel update..." -ForegroundColor Yellow
    Start-Process msiexec.exe -ArgumentList "/i `"$kernelUpdatePath`" /quiet /norestart" -Wait -NoNewWindow
    Write-Host "   ✅ Kernel update installed" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Failed to download/install kernel update: $_" -ForegroundColor Yellow
    Write-Host "   You may need to download manually from:" -ForegroundColor Gray
    Write-Host "   https://aka.ms/wsl2kernel" -ForegroundColor Cyan
}
Write-Host ""

# Step 3: Set WSL default version to 2
Write-Host "[3/6] Setting WSL default version to 2..." -ForegroundColor Cyan
try {
    $wslSetResult = wsl --set-default-version 2 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ WSL default version set to 2" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Could not set default version (may need restart): $wslSetResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  wsl command failed (expected if WSL not fully initialized)" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Start WSL service
Write-Host "[4/6] Starting WSL service..." -ForegroundColor Cyan
try {
    $lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
    if ($lxssService) {
        if ($lxssService.Status -ne 'Running') {
            Start-Service -Name $lxssService.Name -ErrorAction Stop
            Write-Host "   ✅ WSL service started" -ForegroundColor Green
        } else {
            Write-Host "   ✅ WSL service already running" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️  WSL service not found (may need restart)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Could not start WSL service: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Install/Update Ubuntu
Write-Host "[5/6] Checking Ubuntu installation..." -ForegroundColor Cyan
$ubuntuPackages = Get-AppxPackage -Name "*ubuntu*" -ErrorAction SilentlyContinue
if ($ubuntuPackages) {
    Write-Host "   ✅ Ubuntu is installed:" -ForegroundColor Green
    foreach ($pkg in $ubuntuPackages) {
        Write-Host "      - $($pkg.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "   ⚠️  Ubuntu not found, attempting to install..." -ForegroundColor Yellow
    try {
        wsl --install -d Ubuntu 2>&1 | Out-Null
        Write-Host "   ✅ Ubuntu installation initiated" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Could not install Ubuntu automatically" -ForegroundColor Yellow
        Write-Host "   Please install from Microsoft Store:" -ForegroundColor Cyan
        Write-Host "   https://www.microsoft.com/store/productId/9PDXGNCFSCZV" -ForegroundColor Cyan
    }
}
Write-Host ""

# Step 6: Verify installation
Write-Host "[6/6] Verifying installation..." -ForegroundColor Cyan
$allGood = $true

# Check WSL executable
if (Test-Path "C:\Windows\System32\wsl.exe") {
    Write-Host "   ✅ wsl.exe exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ wsl.exe not found" -ForegroundColor Red
    $allGood = $false
}

# Check service
$lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
if ($lxssService -and $lxssService.Status -eq 'Running') {
    Write-Host "   ✅ WSL service is running" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  WSL service not running (may need restart)" -ForegroundColor Yellow
}

# Try WSL command
try {
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $wslVersion -notmatch "|~~b") {
        Write-Host "   ✅ wsl --version works" -ForegroundColor Green
        Write-Host "   Output: $wslVersion" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  wsl --version still failing (may need restart)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  wsl command still not working (may need restart)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allGood) {
    Write-Host "✅ WSL components installed/updated" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: RESTART REQUIRED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restart:" -ForegroundColor White
    Write-Host "  1. Run: wsl --version" -ForegroundColor Cyan
    Write-Host "  2. If successful, run: .\scripts\test_auto.ps1" -ForegroundColor Cyan
    Write-Host "  3. If still failing, run: wsl --install -d Ubuntu" -ForegroundColor Cyan
    Write-Host ""
    
    $restart = Read-Host "Restart now? (Y/N)"
    if ($restart -eq "Y" -or $restart -eq "y") {
        Write-Host "Restarting in 5 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Restart-Computer -Force
    }
} else {
    Write-Host "⚠️  Some components may need manual attention" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Restart your computer" -ForegroundColor Cyan
    Write-Host "  2. After restart, run: wsl --install -d Ubuntu" -ForegroundColor Cyan
    Write-Host "  3. If still failing, check Windows Update for WSL updates" -ForegroundColor Cyan
}

Write-Host ""
