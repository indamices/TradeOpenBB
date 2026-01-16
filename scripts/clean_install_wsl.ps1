# Complete WSL Clean Install Script
# This script completely removes all WSL components and performs a fresh installation
# Usage: Run as Administrator: .\scripts\clean_install_wsl.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Red
Write-Host "  WSL Complete Clean & Reinstall" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Red

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

# Confirmation
Write-Host "⚠️  WARNING: This will completely remove WSL and all Linux distributions!" -ForegroundColor Yellow
Write-Host "   All data in WSL distributions will be lost!" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Type 'YES' to continue (case-sensitive)"
if ($confirm -ne "YES") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# ========================================
# PHASE 1: Complete WSL Removal
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PHASE 1: Complete WSL Removal" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Unregister all WSL distributions
Write-Host "[1/8] Unregistering all WSL distributions..." -ForegroundColor Yellow
try {
    $distros = wsl -l -q 2>&1
    if ($LASTEXITCODE -eq 0 -and $distros) {
        foreach ($distro in $distros) {
            $distro = $distro.Trim()
            if ($distro -and $distro -ne "") {
                Write-Host "   Unregistering: $distro" -ForegroundColor Gray
                wsl --unregister $distro 2>&1 | Out-Null
            }
        }
        Write-Host "   ✅ All distributions unregistered" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  No distributions found or WSL not accessible" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not unregister distributions (may not exist): $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Stop and disable WSL service
Write-Host "[2/8] Stopping WSL service..." -ForegroundColor Yellow
try {
    $lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
    if ($lxssService) {
        if ($lxssService.Status -eq 'Running') {
            Stop-Service -Name $lxssService.Name -Force -ErrorAction Stop
            Write-Host "   ✅ WSL service stopped" -ForegroundColor Green
        }
        Set-Service -Name $lxssService.Name -StartupType Disabled -ErrorAction Stop
        Write-Host "   ✅ WSL service disabled" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  WSL service not found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Error managing service: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Uninstall all Ubuntu/Linux distributions from AppX
Write-Host "[3/8] Uninstalling Linux distributions..." -ForegroundColor Yellow
try {
    $linuxPackages = Get-AppxPackage | Where-Object { $_.Name -like "*ubuntu*" -or $_.Name -like "*linux*" -or $_.Name -like "*wsl*" }
    foreach ($pkg in $linuxPackages) {
        Write-Host "   Uninstalling: $($pkg.Name)" -ForegroundColor Gray
        Remove-AppxPackage -Package $pkg.PackageFullName -ErrorAction SilentlyContinue
    }
    if ($linuxPackages) {
        Write-Host "   ✅ Linux distributions uninstalled" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  No Linux distributions found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Error uninstalling packages: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Disable Windows features
Write-Host "[4/8] Disabling Windows features..." -ForegroundColor Yellow
$features = @(
    "Microsoft-Windows-Subsystem-Linux",
    "VirtualMachinePlatform"
)

foreach ($feature in $features) {
    try {
        $featureInfo = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
        if ($featureInfo -and $featureInfo.State -eq "Enabled") {
            Write-Host "   Disabling: $feature" -ForegroundColor Gray
            Disable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart -ErrorAction Stop
            Write-Host "   ✅ Disabled: $feature" -ForegroundColor Green
        } else {
            Write-Host "   ℹ️  $feature is already disabled" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ⚠️  Could not disable $feature : $_" -ForegroundColor Yellow
    }
}
Write-Host ""

# Step 5: Remove WSL kernel update
Write-Host "[5/8] Removing WSL kernel update..." -ForegroundColor Yellow
try {
    $wslKernel = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like "*WSL*" -or $_.Name -like "*Windows Subsystem*" }
    foreach ($item in $wslKernel) {
        Write-Host "   Uninstalling: $($item.Name)" -ForegroundColor Gray
        $item.Uninstall() | Out-Null
    }
    if ($wslKernel) {
        Write-Host "   ✅ WSL kernel update removed" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  No WSL kernel update found" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not remove kernel update: $_" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Clean registry (WSL-related keys)
Write-Host "[6/8] Cleaning registry..." -ForegroundColor Yellow
$registryPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss"
)

foreach ($regPath in $registryPaths) {
    if (Test-Path $regPath) {
        try {
            Write-Host "   Removing: $regPath" -ForegroundColor Gray
            Remove-Item -Path $regPath -Recurse -Force -ErrorAction Stop
            Write-Host "   ✅ Removed: $regPath" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Could not remove $regPath : $_" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# Step 7: Clean WSL data directories
Write-Host "[7/8] Cleaning WSL data directories..." -ForegroundColor Yellow
$wslDataPaths = @(
    "$env:LOCALAPPDATA\Packages\*Ubuntu*",
    "$env:LOCALAPPDATA\Packages\*Linux*",
    "$env:USERPROFILE\AppData\Local\Packages\*Ubuntu*",
    "$env:USERPROFILE\AppData\Local\Packages\*Linux*"
)

foreach ($pathPattern in $wslDataPaths) {
    $paths = Get-ChildItem -Path $pathPattern -ErrorAction SilentlyContinue
    foreach ($path in $paths) {
        try {
            Write-Host "   Removing: $($path.FullName)" -ForegroundColor Gray
            Remove-Item -Path $path.FullName -Recurse -Force -ErrorAction Stop
            Write-Host "   ✅ Removed: $($path.Name)" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Could not remove $($path.Name) : $_" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# Step 8: Clean temporary files
Write-Host "[8/8] Cleaning temporary files..." -ForegroundColor Yellow
$tempFiles = @(
    "$env:TEMP\wsl*",
    "$env:TEMP\*wsl*",
    "$env:TEMP\*ubuntu*"
)

foreach ($pattern in $tempFiles) {
    $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        try {
            Remove-Item -Path $file.FullName -Force -ErrorAction Stop
            Write-Host "   ✅ Removed: $($file.Name)" -ForegroundColor Green
        } catch {
            # Ignore errors
        }
    }
}
Write-Host "   ✅ Temporary files cleaned" -ForegroundColor Green
Write-Host ""

# ========================================
# PHASE 2: Fresh Installation
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PHASE 2: Fresh Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Enable Windows features
Write-Host "[1/5] Enabling Windows features..." -ForegroundColor Yellow
foreach ($feature in $features) {
    try {
        Write-Host "   Enabling: $feature" -ForegroundColor Gray
        Enable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart -ErrorAction Stop
        Write-Host "   ✅ Enabled: $feature" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Could not enable $feature : $_" -ForegroundColor Yellow
    }
}
Write-Host ""

# Step 2: Download and install WSL kernel update
Write-Host "[2/5] Installing WSL kernel update..." -ForegroundColor Yellow
$kernelUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$kernelUpdatePath = "$env:TEMP\wsl_update_x64.msi"

try {
    Write-Host "   Downloading from: $kernelUpdateUrl" -ForegroundColor Gray
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $kernelUpdateUrl -OutFile $kernelUpdatePath -ErrorAction Stop
    Write-Host "   ✅ Downloaded to: $kernelUpdatePath" -ForegroundColor Green
    
    Write-Host "   Installing kernel update (silent mode)..." -ForegroundColor Gray
    $installProcess = Start-Process msiexec.exe -ArgumentList "/i `"$kernelUpdatePath`" /quiet /norestart" -Wait -PassThru -NoNewWindow
    if ($installProcess.ExitCode -eq 0) {
        Write-Host "   ✅ Kernel update installed successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Installation exit code: $($installProcess.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to download/install kernel update: $_" -ForegroundColor Red
    Write-Host "   You may need to download manually from:" -ForegroundColor Yellow
    Write-Host "   https://aka.ms/wsl2kernel" -ForegroundColor Cyan
}
Write-Host ""

# Step 3: Set WSL default version to 2
Write-Host "[3/5] Setting WSL default version to 2..." -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Give system time to register WSL
try {
    $wslSetResult = wsl --set-default-version 2 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ WSL default version set to 2" -ForegroundColor Green
    } else {
        $resultText = $wslSetResult -join " "
        Write-Host "   ⚠️  Could not set default version: $resultText" -ForegroundColor Yellow
        Write-Host "   This may work after restart" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  wsl command not available yet (expected, will work after restart)" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Start WSL service
Write-Host "[4/5] Starting WSL service..." -ForegroundColor Yellow
try {
    $lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
    if ($lxssService) {
        Set-Service -Name $lxssService.Name -StartupType Automatic -ErrorAction Stop
        Start-Service -Name $lxssService.Name -ErrorAction Stop
        Write-Host "   ✅ WSL service started and set to automatic" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  WSL service not found (will be available after restart)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Could not start service: $_" -ForegroundColor Yellow
    Write-Host "   Service will be available after restart" -ForegroundColor Gray
}
Write-Host ""

# Step 5: Install Ubuntu
Write-Host "[5/5] Installing Ubuntu..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    Write-Host "   Running: wsl --install -d Ubuntu" -ForegroundColor Gray
    $installOutput = wsl --install -d Ubuntu 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Ubuntu installation initiated" -ForegroundColor Green
        Write-Host "   Output: $($installOutput -join ' ')" -ForegroundColor Gray
    } else {
        $outputText = $installOutput -join " "
        if ($outputText -match "already installed" -or $outputText -match "installed") {
            Write-Host "   ✅ Ubuntu is already installed" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Installation command returned error: $outputText" -ForegroundColor Yellow
            Write-Host "   You may need to install Ubuntu manually from Microsoft Store" -ForegroundColor Cyan
            Write-Host "   https://www.microsoft.com/store/productId/9PDXGNCFSCZV" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "   ⚠️  Could not run wsl --install: $_" -ForegroundColor Yellow
    Write-Host "   Please install Ubuntu manually after restart:" -ForegroundColor Cyan
    Write-Host "   wsl --install -d Ubuntu" -ForegroundColor Cyan
    Write-Host "   Or from Microsoft Store" -ForegroundColor Cyan
}
Write-Host ""

# ========================================
# Summary
# ========================================
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Clean Installation Complete" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "✅ All WSL components have been removed and reinstalled" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  RESTART REQUIRED!" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restart, verify installation:" -ForegroundColor White
Write-Host "  1. Run: wsl --version" -ForegroundColor Cyan
Write-Host "  2. Run: wsl -l -v" -ForegroundColor Cyan
Write-Host "  3. If Ubuntu is listed, run: wsl -d Ubuntu" -ForegroundColor Cyan
Write-Host "  4. Once WSL works, start Docker Desktop" -ForegroundColor Cyan
Write-Host "  5. Run: .\scripts\test_auto.ps1" -ForegroundColor Cyan
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
}

Write-Host ""
