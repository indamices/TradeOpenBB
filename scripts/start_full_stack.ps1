# 启动完整的前后端服务
$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TradeOpenBB 全栈启动" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 检查后端是否运行
Write-Host "[检查] 后端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✓ 后端服务已运行" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "  ✗ 后端服务未运行" -ForegroundColor Red
    Write-Host "  提示: 请先运行 backend\start_server.bat 启动后端" -ForegroundColor Yellow
    $backendRunning = $false
}

# 检查 Node.js
Write-Host "`n[检查] Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js 未安装" -ForegroundColor Red
    Write-Host "  请先安装 Node.js: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# 检查前端依赖
Write-Host "`n[检查] 前端依赖..." -ForegroundColor Yellow
Set-Location $ProjectRoot

if (-not (Test-Path "node_modules")) {
    Write-Host "  安装前端依赖..." -ForegroundColor Gray
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "  ✓ 依赖已安装" -ForegroundColor Green
}

# 创建 .env.local
Write-Host "`n[配置] 环境变量..." -ForegroundColor Yellow
$envFile = ".env.local"
if (-not (Test-Path $envFile)) {
    "VITE_API_BASE_URL=http://localhost:8000" | Out-File -FilePath $envFile -Encoding utf8 -NoNewline
    Write-Host "  ✓ .env.local 已创建" -ForegroundColor Green
    Write-Host "    API_BASE_URL=http://localhost:8000" -ForegroundColor Gray
} else {
    Write-Host "  ✓ .env.local 已存在" -ForegroundColor Green
    $envContent = Get-Content $envFile
    if ($envContent -notmatch "VITE_API_BASE_URL") {
        Add-Content -Path $envFile -Value "`nVITE_API_BASE_URL=http://localhost:8000"
        Write-Host "   已添加 VITE_API_BASE_URL" -ForegroundColor Gray
    }
}

# 启动前端
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  前端启动中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n  前端地址: http://localhost:3000" -ForegroundColor Cyan
if ($backendRunning) {
    Write-Host "  后端地址: http://localhost:8000" -ForegroundColor Cyan
} else {
    Write-Host "  后端地址: 未运行 (请先启动后端)" -ForegroundColor Yellow
}
Write-Host "`n  按 Ctrl+C 停止前端`n" -ForegroundColor Yellow

npm run dev
