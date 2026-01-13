# PowerShell script to update WSL
# Usage: .\update_wsl.ps1
# Note: May require administrator privileges

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  更新 Windows Subsystem for Linux (WSL)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  此操作可能需要管理员权限" -ForegroundColor Yellow
    Write-Host "如果更新失败，请以管理员身份运行 PowerShell 并执行:" -ForegroundColor Yellow
    Write-Host "  wsl --update" -ForegroundColor Cyan
    Write-Host ""
}

# Step 1: Check current WSL version
Write-Host "[1] 检查当前 WSL 版本..." -ForegroundColor Yellow
try {
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "当前版本:" -ForegroundColor Gray
        $wslVersion | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "无法获取 WSL 版本信息" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WSL 可能未安装或版本过旧" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Update WSL
Write-Host "[2] 更新 WSL..." -ForegroundColor Yellow
Write-Host "这可能需要几分钟时间，请耐心等待...`n" -ForegroundColor Gray

try {
    $updateOutput = wsl --update 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "✅ WSL 更新成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "更新输出:" -ForegroundColor Gray
        $updateOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "❌ WSL 更新失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "错误信息:" -ForegroundColor Red
        $updateOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "可能的解决方案:" -ForegroundColor Yellow
        Write-Host "  1. 以管理员身份运行 PowerShell" -ForegroundColor White
        Write-Host "  2. 手动运行: wsl --update" -ForegroundColor White
        Write-Host "  3. 检查网络连接" -ForegroundColor White
        Write-Host "  4. 重启电脑后重试" -ForegroundColor White
    }
} catch {
    Write-Host "❌ 更新过程中出现错误: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请尝试以管理员身份运行此脚本" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Check WSL status after update
Write-Host "[3] 检查更新后的 WSL 状态..." -ForegroundColor Yellow
try {
    $wslStatus = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "WSL 状态:" -ForegroundColor Gray
        $wslStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    }
} catch {
    Write-Host "无法获取 WSL 状态" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  更新完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 如果更新成功，重启 Docker Desktop" -ForegroundColor White
Write-Host "  2. 然后运行: .\start_docker.ps1" -ForegroundColor White
Write-Host ""
