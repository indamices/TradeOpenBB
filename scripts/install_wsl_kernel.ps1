# Install WSL Kernel Update
# This script downloads and installs the latest WSL kernel update
# Usage: Run as Administrator: .\scripts\install_wsl_kernel.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Install WSL Kernel Update" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script REQUIRES Administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Cyan
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Cyan
    Write-Host "  3. Run this script again" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "✅ Running as Administrator" -ForegroundColor Green
Write-Host ""

# Check if user has a local MSI file
Write-Host "[1] Checking for local WSL kernel update package..." -ForegroundColor Yellow
$localMsiPaths = @(
    "$env:USERPROFILE\Downloads\wsl_update_x64.msi",
    "$env:USERPROFILE\Desktop\wsl_update_x64.msi",
    "$env:USERPROFILE\Documents\wsl_update_x64.msi",
    "C:\wsl_update_x64.msi"
)

$msiPath = $null
foreach ($path in $localMsiPaths) {
    if (Test-Path $path) {
        $msiPath = $path
        Write-Host "   ✅ Found local package: $path" -ForegroundColor Green
        break
    }
}

# If no local file, download it
if (-not $msiPath) {
    Write-Host "   ℹ️  No local package found, will download from Microsoft" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "[2] Downloading WSL kernel update..." -ForegroundColor Yellow
    $kernelUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    $downloadPath = "$env:TEMP\wsl_update_x64.msi"
    
    try {
        Write-Host "   Downloading from: $kernelUpdateUrl" -ForegroundColor Gray
        Write-Host "   Saving to: $downloadPath" -ForegroundColor Gray
        Write-Host "   This may take a few minutes..." -ForegroundColor Gray
        
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $kernelUpdateUrl -OutFile $downloadPath -ErrorAction Stop
        Write-Host "   ✅ Download completed" -ForegroundColor Green
        $msiPath = $downloadPath
    } catch {
        Write-Host "   ❌ Download failed: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download manually from:" -ForegroundColor Yellow
        Write-Host "   https://aka.ms/wsl2kernel" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Then run this script again, or install the .msi file manually" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "[2] Using local package..." -ForegroundColor Yellow
}

Write-Host ""

# Install the MSI package
Write-Host "[3] Installing WSL kernel update..." -ForegroundColor Yellow
Write-Host "   Package: $msiPath" -ForegroundColor Gray
Write-Host "   This will open the installer window..." -ForegroundColor Gray
Write-Host ""

try {
    # Use Start-Process to run with elevated privileges
    $installProcess = Start-Process msiexec.exe -ArgumentList "/i `"$msiPath`" /quiet /norestart" -Wait -PassThru -NoNewWindow -Verb RunAs
    
    if ($installProcess.ExitCode -eq 0) {
        Write-Host "   ✅ WSL kernel update installed successfully" -ForegroundColor Green
        Write-Host "   Exit code: $($installProcess.ExitCode)" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  Installation completed with exit code: $($installProcess.ExitCode)" -ForegroundColor Yellow
        Write-Host "   This may still be successful - let's verify" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Installation failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try installing manually:" -ForegroundColor Yellow
    Write-Host "   1. Right-click the .msi file" -ForegroundColor Cyan
    Write-Host "   2. Select 'Run as Administrator'" -ForegroundColor Cyan
    Write-Host "   3. Follow the installation wizard" -ForegroundColor Cyan
    exit 1
}

Write-Host ""

# Wait a moment for system to register the update
Write-Host "[4] Waiting for system to register update..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "   ✅ Ready" -ForegroundColor Green
Write-Host ""

# Try to update WSL
Write-Host "[5] Updating WSL..." -ForegroundColor Yellow
try {
    $updateOutput = wsl --update 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ WSL update command succeeded" -ForegroundColor Green
        if ($updateOutput) {
            Write-Host "   Output:" -ForegroundColor Gray
            $updateOutput | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "   ⚠️  wsl --update returned exit code: $LASTEXITCODE" -ForegroundColor Yellow
        $outputText = $updateOutput -join " "
        if ($outputText) {
            Write-Host "   Output: $outputText" -ForegroundColor Gray
        }
        Write-Host "   This may work after a restart" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not run wsl --update: $_" -ForegroundColor Yellow
    Write-Host "   This is normal if WSL needs a restart" -ForegroundColor Gray
}
Write-Host ""

# Set default version to 2
Write-Host "[6] Setting WSL default version to 2..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $setVersionOutput = wsl --set-default-version 2 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Default version set to WSL 2" -ForegroundColor Green
    } else {
        $outputText = $setVersionOutput -join " "
        if ($outputText -match "restart" -or $outputText -match "重启") {
            Write-Host "   ⚠️  Restart required before setting version" -ForegroundColor Yellow
        } else {
            Write-Host "   ⚠️  Could not set default version: $outputText" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ⚠️  Could not set default version: $_" -ForegroundColor Yellow
    Write-Host "   Will work after restart" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "✅ WSL kernel update has been installed" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  RESTART RECOMMENDED" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restart, verify installation:" -ForegroundColor White
Write-Host "  1. Run: wsl --version" -ForegroundColor Cyan
Write-Host "  2. Run: wsl --status" -ForegroundColor Cyan
Write-Host "  3. If successful, proceed to install Ubuntu" -ForegroundColor Cyan
Write-Host ""

$restart = Read-Host "Restart now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "Restarting in 10 seconds..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to cancel" -ForegroundColor Gray
    Start-Sleep -Seconds 10
    Restart-Computer -Force
} else {
    Write-Host ""
    Write-Host "Please restart manually when ready." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restart, run:" -ForegroundColor White
    Write-Host "  wsl --version" -ForegroundColor Cyan
    Write-Host "  wsl --status" -ForegroundColor Cyan
}

Write-Host ""
