# Simple start and test script
$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  启动服务并运行测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Clean up
Write-Host "[1] 清理旧服务..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.MainWindowTitle -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object {$_.ProcessName -eq "node"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Step 2: Setup environment
Write-Host "[2] 设置环境..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@ | Out-File -FilePath "backend\.env" -Encoding utf8
}

Set-Location backend
$initCmd = 'import sys; sys.path.insert(0, "."); from database import init_db; init_db()'
python -c $initCmd 2>&1 | Out-Null
Set-Location ..
Write-Host "✅ 环境设置完成" -ForegroundColor Green

# Step 3: Start backend
Write-Host "`n[3] 启动后端服务..." -ForegroundColor Yellow
$backendScript = @"
cd '$PSScriptRoot\backend'
Write-Host '后端服务启动中...' -ForegroundColor Green
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"@
$backendScript | Out-File -FilePath "$env:TEMP\start_backend.ps1" -Encoding utf8
Start-Process powershell -ArgumentList "-NoExit", "-File", "$env:TEMP\start_backend.ps1"
Write-Host "✅ 后端服务启动命令已执行" -ForegroundColor Green

# Step 4: Wait for backend
Write-Host "`n[4] 等待后端启动..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $ready = $true
        Write-Host "✅ 后端服务已就绪！" -ForegroundColor Green
    } catch {
        if ($attempt % 5 -eq 0) {
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
}

if (-not $ready) {
    Write-Host "`n⚠️  后端服务启动超时" -ForegroundColor Yellow
    Write-Host "   请检查新打开的 PowerShell 窗口中的错误信息" -ForegroundColor Gray
    Write-Host "   或手动运行: cd backend; python -m uvicorn main:app --reload" -ForegroundColor Gray
    exit 1
}

# Step 5: Run tests
Write-Host "`n[5] 运行快速测试..." -ForegroundColor Yellow
Write-Host ("=" * 50) -ForegroundColor Gray

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Health check
Write-Host "`n[测试 1] 健康检查..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get -TimeoutSec 5
    Write-Host "✅ 通过: $($response.message)" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}

# Test 2: Create portfolio
Write-Host "`n[测试 2] 创建投资组合..." -ForegroundColor Cyan
try {
    $body = @{name="测试组合"; initial_cash=100000.0} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/portfolio" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5
    $portfolioId = $response.id
    Write-Host "✅ 通过: ID=$portfolioId, 名称=$($response.name)" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
    $portfolioId = 1
}

# Test 3: Get portfolio
Write-Host "`n[测试 3] 获取投资组合..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/portfolio?portfolio_id=$portfolioId" -Method Get -TimeoutSec 5
    Write-Host "✅ 通过: $($response.name), 现金=$($response.current_cash)" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}

# Test 4: Create order
Write-Host "`n[测试 4] 创建订单..." -ForegroundColor Cyan
try {
    $body = @{portfolio_id=$portfolioId; symbol="AAPL"; side="BUY"; type="MARKET"; quantity=10} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/orders" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5
    Write-Host "✅ 通过: ID=$($response.id), 符号=$($response.symbol)" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}

# Test 5: Get orders
Write-Host "`n[测试 5] 获取订单列表..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/orders?portfolio_id=$portfolioId" -Method Get -TimeoutSec 5
    Write-Host "✅ 通过: 共 $($response.Count) 个订单" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host "`n" + ("=" * 50) -ForegroundColor Gray
Write-Host "`n测试结果汇总:" -ForegroundColor Cyan
Write-Host "  通过: $passed" -ForegroundColor Green
Write-Host "  失败: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  总计: $($passed + $failed)" -ForegroundColor White

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  服务信息" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "后端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "API 文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "  • 服务在独立的 PowerShell 窗口中运行" -ForegroundColor Gray
Write-Host "  • 访问 http://localhost:8000/docs 进行交互式测试" -ForegroundColor Gray
Write-Host "  • 查看 MANUAL_TESTING_GUIDE.md 获取详细测试指南" -ForegroundColor Gray
Write-Host ""
