# Start services for manual testing
$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  启动服务进行手动测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if ports are in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return $connection
    } catch {
        return $false
    }
}

$backendPort = 8000
$frontendPort = 5173

# Check backend port
if (Test-Port -Port $backendPort) {
    Write-Host "⚠️  端口 $backendPort 已被占用" -ForegroundColor Yellow
    $useExisting = Read-Host "使用现有后端服务? (y/n)"
    if ($useExisting -ne "y") {
        Write-Host "请先停止占用端口 $backendPort 的服务" -ForegroundColor Red
        exit 1
    }
    $backendRunning = $true
} else {
    $backendRunning = $false
}

# Check frontend port
if (Test-Port -Port $frontendPort) {
    Write-Host "⚠️  端口 $frontendPort 已被占用" -ForegroundColor Yellow
    $useExisting = Read-Host "使用现有前端服务? (y/n)"
    if ($useExisting -ne "y") {
        Write-Host "请先停止占用端口 $frontendPort 的服务" -ForegroundColor Red
        exit 1
    }
    $frontendRunning = $true
} else {
    $frontendRunning = $false
}

# Start Backend
if (-not $backendRunning) {
    Write-Host "`n🚀 启动后端服务..." -ForegroundColor Green
    
    # Check Python
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Python 未安装或不在 PATH 中" -ForegroundColor Red
        exit 1
    }
    
    # Check .env
    if (-not (Test-Path "backend\.env")) {
        Write-Host "创建 backend\.env 文件..." -ForegroundColor Yellow
        @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
    }
    
    # Initialize database
    Write-Host "初始化数据库..." -ForegroundColor Yellow
    Set-Location backend
    $initCmd = 'import sys; sys.path.insert(0, "."); from database import init_db; init_db(); print("Database initialized")'
    python -c $initCmd 2>&1 | Out-Null
    Set-Location ..
    
    # Start backend
    Write-Host "启动后端: http://localhost:$backendPort" -ForegroundColor Cyan
    Write-Host "API 文档: http://localhost:$backendPort/docs" -ForegroundColor Cyan
    Write-Host ""
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    
    # Wait for backend
    Write-Host "等待后端启动..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    $ready = $false
    
    while ($attempt -lt $maxAttempts -and -not $ready) {
        Start-Sleep -Seconds 1
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$backendPort" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
            $ready = $true
            Write-Host "✅ 后端已就绪!" -ForegroundColor Green
        } catch {
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    
    if (-not $ready) {
        Write-Host "`n⚠️  后端启动较慢，请检查新打开的窗口" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ 使用现有后端服务 (端口 $backendPort)" -ForegroundColor Green
}

# Start Frontend
if (-not $frontendRunning) {
    Write-Host "`n🚀 启动前端服务..." -ForegroundColor Green
    
    # Check Node.js
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️  Node.js 未安装，跳过前端启动" -ForegroundColor Yellow
        Write-Host "   可以稍后手动运行: npm run dev" -ForegroundColor Yellow
    } else {
        # Check node_modules
        if (-not (Test-Path "node_modules")) {
            Write-Host "安装前端依赖..." -ForegroundColor Yellow
            npm install
        }
        
        Write-Host "启动前端: http://localhost:$frontendPort" -ForegroundColor Cyan
        Write-Host ""
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; npm run dev"
        
        Start-Sleep -Seconds 2
        Write-Host "✅ 前端正在启动!" -ForegroundColor Green
    }
} else {
    Write-Host "✅ 使用现有前端服务 (端口 $frontendPort)" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  服务运行中" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后端 API:  http://localhost:$backendPort" -ForegroundColor White
Write-Host "API 文档:  http://localhost:$backendPort/docs" -ForegroundColor White
Write-Host "前端界面: http://localhost:$frontendPort" -ForegroundColor White
Write-Host ""
Write-Host "📋 测试指南:" -ForegroundColor Cyan
Write-Host "  1. 打开浏览器访问 API 文档: http://localhost:$backendPort/docs" -ForegroundColor Yellow
Write-Host "  2. 在 API 文档中可以直接测试所有端点" -ForegroundColor Yellow
Write-Host "  3. 查看 MANUAL_TESTING_GUIDE.md 获取详细测试步骤" -ForegroundColor Yellow
Write-Host ""
Write-Host "按任意键退出（服务将继续运行）..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
