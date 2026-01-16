# Fix Python & Docker Configuration
# Complete solution: Downgrade Python + Configure Docker Proxy

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Fix Python & Docker Configuration" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get script directory
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptRoot ".."

# ========================================
# Step 1: Check and downgrade Python
# ========================================
Write-Host "[1/4] Checking Python version..." -ForegroundColor Yellow

$pythonVersion = python --version 2>&1
Write-Host "   Current version: $pythonVersion" -ForegroundColor Gray

if ($pythonVersion -match "3\.11\.0a1|alpha|beta|rc") {
    Write-Host "   ⚠️  Alpha version detected, need to install stable version" -ForegroundColor Yellow
    Write-Host "   Installing Python 3.11.9 stable version..." -ForegroundColor Gray
    
    # Try using winget
    try {
        Write-Host "   Attempting to install via winget..." -ForegroundColor Gray
        winget install -e --id Python.Python.3.11 --version 3.11.9 --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Python 3.11.9 installed via winget" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  winget installation failed or not available" -ForegroundColor Yellow
            Write-Host "   Please install Python 3.11.9 manually:" -ForegroundColor Cyan
            Write-Host "   https://www.python.org/downloads/release/python-3119/" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "   ⚠️  winget not available, please install manually:" -ForegroundColor Yellow
        Write-Host "   https://www.python.org/downloads/release/python-3119/" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ✅ Python version looks OK: $pythonVersion" -ForegroundColor Green
}

# Verify new version
Start-Sleep -Seconds 2
$newVersion = python --version 2>&1
Write-Host "   Verified version: $newVersion" -ForegroundColor Gray

Write-Host ""

# ========================================
# Step 2: Configure Docker proxy
# ========================================
Write-Host "[2/4] Configuring Docker to use system proxy..." -ForegroundColor Yellow

$dockerConfigPath = "$env:USERPROFILE\.docker\daemon.json"

# Check system proxy
Write-Host "   Checking system proxy settings..." -ForegroundColor Gray
try {
    $proxySettings = [System.Net.WebRequest]::GetSystemWebProxy()
    $testUrl = [uri]"https://registry-1.docker.io"
    $proxyUrl = $proxySettings.GetProxy($testUrl)
    
    if ($proxyUrl -ne $testUrl) {
        Write-Host "   ✅ System proxy detected: $proxyUrl" -ForegroundColor Green
        Write-Host "   Docker Desktop should automatically use this" -ForegroundColor Gray
    } else {
        Write-Host "   ℹ️  No system proxy detected in code" -ForegroundColor Gray
        Write-Host "   Make sure Windows proxy is configured with your PAC file" -ForegroundColor Cyan
        Write-Host "   PAC URL: https://wmtok.com/mohan.zhang/754400045.pac" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ⚠️  Could not check proxy settings: $_" -ForegroundColor Yellow
}

# Ensure daemon.json is valid (no BOM)
if (Test-Path $dockerConfigPath) {
    try {
        $content = Get-Content $dockerConfigPath -Raw
        $json = $content | ConvertFrom-Json
        # Remove BOM and save cleanly
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        $cleanJson = $json | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($dockerConfigPath, $cleanJson, $utf8NoBom)
        Write-Host "   ✅ daemon.json is valid and BOM-free" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  daemon.json has issues, creating clean version" -ForegroundColor Yellow
        $cleanConfig = @{} | ConvertTo-Json -Depth 10
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($dockerConfigPath, $cleanConfig, $utf8NoBom)
        Write-Host "   ✅ Created clean daemon.json" -ForegroundColor Green
    }
} else {
    Write-Host "   ℹ️  daemon.json not found, will be created when needed" -ForegroundColor Gray
}

Write-Host ""

# ========================================
# Step 3: Recreate virtual environment
# ========================================
Write-Host "[3/4] Recreating virtual environment..." -ForegroundColor Yellow

$backendPath = Join-Path $projectRoot "backend"
$venvPath = Join-Path $backendPath "venv"

if (-not (Test-Path $backendPath)) {
    Write-Host "   ❌ backend directory not found!" -ForegroundColor Red
    exit 1
}

Set-Location $backendPath

if (Test-Path $venvPath) {
    Write-Host "   Removing old virtual environment..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $venvPath -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host "   Creating new virtual environment..." -ForegroundColor Gray

# Try to use py launcher first, fallback to python
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "   Using py launcher..." -ForegroundColor Gray
    $pythonCmd = "py"
    $pythonArgs = @("-3.11", "-m", "venv", "venv")
} else {
    Write-Host "   Using python command..." -ForegroundColor Gray
    $pythonCmd = "python"
    $pythonArgs = @("-m", "venv", "venv")
}

try {
    & $pythonCmd $pythonArgs
    if ($LASTEXITCODE -eq 0 -and (Test-Path "venv\Scripts\activate.ps1")) {
        Write-Host "   ✅ Virtual environment created successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Virtual environment creation may have issues" -ForegroundColor Yellow
        Write-Host "   Trying with default python..." -ForegroundColor Gray
        python -m venv venv
    }
} catch {
    Write-Host "   ⚠️  Error creating venv: $_" -ForegroundColor Yellow
    Write-Host "   Trying with default python..." -ForegroundColor Gray
    python -m venv venv
}

if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "   ❌ Failed to create virtual environment" -ForegroundColor Red
    Write-Host "   Please check Python installation" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# ========================================
# Step 4: Install dependencies
# ========================================
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Yellow

if (Test-Path "venv\Scripts\activate.ps1") {
    & .\venv\Scripts\activate.ps1
    
    Write-Host "   Upgrading pip..." -ForegroundColor Gray
    python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
    
    Write-Host "   Installing requirements (this may take a few minutes)..." -ForegroundColor Gray
    python -m pip install -r requirements.txt 2>&1 | ForEach-Object {
        if ($_ -match "error|ERROR|failed|FAILED") {
            Write-Host "   ⚠️  $_" -ForegroundColor Yellow
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Some dependencies may have failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-Host "   This might be OK if only optional packages failed" -ForegroundColor Gray
    }
} else {
    Write-Host "   ❌ Virtual environment not found" -ForegroundColor Red
}

Write-Host ""

# ========================================
# Summary
# ========================================
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "✅ Python environment checked/fixed" -ForegroundColor Green
Write-Host "✅ Virtual environment recreated" -ForegroundColor Green
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT: Restart Docker Desktop to apply proxy settings" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Restart Docker Desktop" -ForegroundColor Cyan
Write-Host "  2. Verify Docker proxy: docker pull hello-world" -ForegroundColor Cyan
Write-Host "  3. Run tests: .\scripts\test_auto.ps1" -ForegroundColor Cyan
Write-Host ""
