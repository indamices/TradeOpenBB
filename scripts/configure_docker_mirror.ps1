# Configure Docker to use Chinese mirror sources
# This helps when Docker Hub is not accessible
# Usage: Run as Administrator: .\scripts\configure_docker_mirror.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Configure Docker Mirror Sources" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script works better with Administrator privileges" -ForegroundColor Yellow
    Write-Host "   Some configurations may require admin rights" -ForegroundColor Gray
    Write-Host ""
}

# Docker Desktop configuration file path
$dockerConfigPath = "$env:USERPROFILE\.docker\daemon.json"

Write-Host "[1] Checking Docker Desktop configuration..." -ForegroundColor Yellow

# Create .docker directory if it doesn't exist
$dockerDir = Split-Path $dockerConfigPath -Parent
if (-not (Test-Path $dockerDir)) {
    New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
    Write-Host "   ✅ Created .docker directory" -ForegroundColor Green
}

# Read existing configuration or create new
$config = @{}
if (Test-Path $dockerConfigPath) {
    try {
        $existingConfig = Get-Content $dockerConfigPath -Raw | ConvertFrom-Json
        $config = $existingConfig | ConvertTo-Json -Depth 10 | ConvertFrom-Json
        Write-Host "   ✅ Found existing configuration" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Could not read existing config, creating new one" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ℹ️  No existing configuration, creating new one" -ForegroundColor Gray
}

Write-Host ""

# Configure registry mirrors (Chinese sources)
Write-Host "[2] Configuring registry mirrors..." -ForegroundColor Yellow

# Common Chinese Docker mirror sources
$mirrors = @(
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
)

if (-not $config.'registry-mirrors') {
    $config | Add-Member -MemberType NoteProperty -Name "registry-mirrors" -Value @() -Force
}

# Add mirrors if not already present
foreach ($mirror in $mirrors) {
    if ($config.'registry-mirrors' -notcontains $mirror) {
        $config.'registry-mirrors' += $mirror
        Write-Host "   ✅ Added mirror: $mirror" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  Mirror already exists: $mirror" -ForegroundColor Gray
    }
}

Write-Host ""

# Save configuration
Write-Host "[3] Saving configuration..." -ForegroundColor Yellow
try {
    $configJson = $config | ConvertTo-Json -Depth 10
    # Use UTF8Encoding without BOM to avoid Docker parsing errors
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($dockerConfigPath, $configJson, $utf8NoBom)
    Write-Host "   ✅ Configuration saved to: $dockerConfigPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Configuration content:" -ForegroundColor Gray
    Write-Host $configJson -ForegroundColor White
} catch {
    Write-Host "   ❌ Failed to save configuration: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Instructions
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Configuration Complete" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "⚠️  IMPORTANT: Restart Docker Desktop for changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Completely close Docker Desktop" -ForegroundColor Cyan
Write-Host "  2. Restart Docker Desktop" -ForegroundColor Cyan
Write-Host "  3. Wait for Docker to fully start" -ForegroundColor Cyan
Write-Host "  4. Run: .\scripts\test_auto.ps1" -ForegroundColor Cyan
Write-Host ""

$restart = Read-Host "Would you like to restart Docker Desktop now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host ""
    Write-Host "Stopping Docker Desktop..." -ForegroundColor Yellow
    Stop-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    
    Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    
    Write-Host "✅ Docker Desktop restart initiated" -ForegroundColor Green
    Write-Host "   Please wait for Docker to fully start (check system tray)" -ForegroundColor Gray
    Write-Host "   Then run: .\scripts\test_auto.ps1" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Please restart Docker Desktop manually, then run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\test_auto.ps1" -ForegroundColor Cyan
}

Write-Host ""
