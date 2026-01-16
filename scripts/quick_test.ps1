# ============================================================================
# 快速测试脚本 - 一键启动和测试
# ============================================================================

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SetupScript = Join-Path $ScriptDir "setup_and_test_local.ps1"
$TestScript = Join-Path $ScriptDir "test_api_endpoints.ps1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TradeOpenBB 快速测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "选择操作:" -ForegroundColor Yellow
Write-Host "  1. 完整设置并启动服务器（首次使用）" -ForegroundColor White
Write-Host "  2. 仅启动服务器（已设置过环境）" -ForegroundColor White
Write-Host "  3. 仅运行 API 测试（服务器需已启动）" -ForegroundColor White
Write-Host "  4. 设置环境但不启动（仅安装依赖）" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请选择 (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n开始完整设置..." -ForegroundColor Green
        & $SetupScript
    }
    "2" {
        Write-Host "`n启动服务器..." -ForegroundColor Green
        $BackendDir = Join-Path (Split-Path -Parent $ScriptDir) "backend"
        $venvActivate = Join-Path $BackendDir "venv\Scripts\Activate.ps1"
        
        if (Test-Path $venvActivate) {
            Set-Location $BackendDir
            & $venvActivate
            Write-Host "服务器启动中..." -ForegroundColor Yellow
            Write-Host "API 文档: http://localhost:8000/docs`n" -ForegroundColor Cyan
            uvicorn main:app --reload --host 0.0.0.0 --port 8000
        } else {
            Write-Host "错误: 未找到虚拟环境，请先运行选项 1" -ForegroundColor Red
        }
    }
    "3" {
        Write-Host "`n运行 API 测试..." -ForegroundColor Green
        & $TestScript
    }
    "4" {
        Write-Host "`n仅设置环境..." -ForegroundColor Green
        # 修改 setup 脚本，在启动服务器前停止
        # 这里简化处理，提示用户手动停止
        Write-Host "注意: 脚本会启动服务器，按 Ctrl+C 停止" -ForegroundColor Yellow
        & $SetupScript
    }
    default {
        Write-Host "无效选择" -ForegroundColor Red
    }
}
