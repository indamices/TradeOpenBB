# Check WSL Status Script
# Comprehensive WSL diagnostic
# Usage: .\scripts\check_wsl_status.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  WSL Status Check" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check 1: WSL executable
Write-Host "[1] Checking WSL executable..." -ForegroundColor Yellow
if (Test-Path "C:\Windows\System32\wsl.exe") {
    Write-Host "   ✅ wsl.exe exists" -ForegroundColor Green
    $wslSize = (Get-Item "C:\Windows\System32\wsl.exe").Length
    Write-Host "   Size: $([math]::Round($wslSize/1KB, 2)) KB" -ForegroundColor Gray
} else {
    Write-Host "   ❌ wsl.exe not found!" -ForegroundColor Red
}
Write-Host ""

# Check 2: WSL service
Write-Host "[2] Checking WSL service..." -ForegroundColor Yellow
$lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
if ($lxssService) {
    Write-Host "   Service found: $($lxssService.Name)" -ForegroundColor Green
    Write-Host "   Status: $($lxssService.Status)" -ForegroundColor $(if ($lxssService.Status -eq 'Running') { 'Green' } else { 'Yellow' })
    if ($lxssService.Status -ne 'Running') {
        Write-Host "   ⚠️  Service is not running!" -ForegroundColor Yellow
        Write-Host "   Attempting to start service..." -ForegroundColor Gray
        try {
            Start-Service -Name $lxssService.Name -ErrorAction Stop
            Write-Host "   ✅ Service started" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Failed to start service: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "   ❌ WSL service (LxssManager) not found!" -ForegroundColor Red
    Write-Host "   This usually means WSL is not properly installed" -ForegroundColor Yellow
}
Write-Host ""

# Check 3: Windows features
Write-Host "[3] Checking Windows features..." -ForegroundColor Yellow
$features = @(
    "Microsoft-Windows-Subsystem-Linux",
    "VirtualMachinePlatform"
)

foreach ($feature in $features) {
    try {
        $featureInfo = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
        if ($featureInfo) {
            $status = if ($featureInfo.State -eq "Enabled") { "✅ Enabled" } else { "❌ Disabled" }
            $color = if ($featureInfo.State -eq "Enabled") { "Green" } else { "Red" }
            Write-Host "   $status $feature" -ForegroundColor $color
        } else {
            Write-Host "   ⚠️  Could not check $feature" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  Error checking $feature" -ForegroundColor Yellow
    }
}
Write-Host ""

# Check 4: Ubuntu installation
Write-Host "[4] Checking Ubuntu installation..." -ForegroundColor Yellow
$ubuntuPackages = Get-AppxPackage -Name "*ubuntu*" -ErrorAction SilentlyContinue
if ($ubuntuPackages) {
    Write-Host "   ✅ Ubuntu packages found:" -ForegroundColor Green
    foreach ($pkg in $ubuntuPackages) {
        Write-Host "      - $($pkg.Name)" -ForegroundColor Gray
        Write-Host "        Location: $($pkg.InstallLocation)" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ No Ubuntu packages found!" -ForegroundColor Red
}
Write-Host ""

# Check 5: Ubuntu executable
Write-Host "[5] Checking Ubuntu executable..." -ForegroundColor Yellow
$ubuntuPaths = @(
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\ubuntu.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\ubuntu*.exe",
    "$env:ProgramFiles\WindowsApps\*\ubuntu.exe"
)

$ubuntuFound = $false
foreach ($path in $ubuntuPaths) {
    $files = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
    if ($files) {
        foreach ($file in $files) {
            Write-Host "   ✅ Found: $($file.FullName)" -ForegroundColor Green
            $ubuntuFound = $true
        }
    }
}

if (-not $ubuntuFound) {
    Write-Host "   ❌ Ubuntu executable not found in common locations" -ForegroundColor Red
}
Write-Host ""

# Check 6: Try to run WSL commands
Write-Host "[6] Testing WSL commands..." -ForegroundColor Yellow
Write-Host "   Testing: wsl --version" -ForegroundColor Gray
try {
    $result = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ wsl --version succeeded" -ForegroundColor Green
        Write-Host "   Output:" -ForegroundColor Gray
        $result | ForEach-Object { Write-Host "      $_" -ForegroundColor White }
    } else {
        Write-Host "   ❌ wsl --version failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "   Output:" -ForegroundColor Gray
        $result | ForEach-Object { Write-Host "      $_" -ForegroundColor Yellow }
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}
Write-Host ""

# Check 7: Docker Desktop WSL integration
Write-Host "[7] Checking Docker Desktop..." -ForegroundColor Yellow
$dockerProcess = Get-Process -Name "*Docker*" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "   ✅ Docker Desktop is running" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Docker Desktop is not running" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$needsRestart = $false

if (-not (Test-Path "C:\Windows\System32\wsl.exe")) {
    Write-Host "❌ WSL executable missing - REINSTALL REQUIRED" -ForegroundColor Red
    $needsRestart = $true
}

$lxssService = Get-Service -Name "*Lxss*" -ErrorAction SilentlyContinue
if (-not $lxssService) {
    Write-Host "❌ WSL service missing - RESTART REQUIRED" -ForegroundColor Red
    $needsRestart = $true
} elseif ($lxssService.Status -ne 'Running') {
    Write-Host "⚠️  WSL service not running - RESTART REQUIRED" -ForegroundColor Yellow
    $needsRestart = $true
}

if ($needsRestart) {
    Write-Host ""
    Write-Host "⚠️  RECOMMENDATION: RESTART YOUR COMPUTER" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After restart:" -ForegroundColor White
    Write-Host "  1. Verify: wsl --version" -ForegroundColor Cyan
    Write-Host "  2. If still failing, run: wsl --install" -ForegroundColor Cyan
    Write-Host "  3. Restart Docker Desktop" -ForegroundColor Cyan
} else {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If WSL commands still fail, try:" -ForegroundColor Yellow
    Write-Host "  1. Restart computer" -ForegroundColor White
    Write-Host "  2. Run: wsl --update" -ForegroundColor Cyan
    Write-Host "  3. Run: wsl --install -d Ubuntu" -ForegroundColor Cyan
}

Write-Host ""
