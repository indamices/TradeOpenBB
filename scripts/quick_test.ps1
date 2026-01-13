# Quick test script - Test basic endpoints
$baseUrl = "http://localhost:8000"

Write-Host "`n快速测试 API 端点..." -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Test 1: Health check
Write-Host "`n[1] 测试健康检查端点..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get
    Write-Host "✅ 健康检查通过: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "❌ 健康检查失败: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Create portfolio
Write-Host "`n[2] 测试创建投资组合..." -ForegroundColor Yellow
try {
    $body = @{
        name = "测试组合"
        initial_cash = 100000.0
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/portfolio" -Method Post -Body $body -ContentType "application/json"
    $portfolioId = $response.id
    Write-Host "✅ 投资组合创建成功: ID=$portfolioId, 名称=$($response.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ 创建投资组合失败: $_" -ForegroundColor Red
    $portfolioId = 1  # Use default
}

# Test 3: Get portfolio
Write-Host "`n[3] 测试获取投资组合..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/portfolio?portfolio_id=$portfolioId" -Method Get
    Write-Host "✅ 获取投资组合成功: $($response.name), 现金=$($response.current_cash)" -ForegroundColor Green
} catch {
    Write-Host "❌ 获取投资组合失败: $_" -ForegroundColor Red
}

# Test 4: Create order
Write-Host "`n[4] 测试创建订单..." -ForegroundColor Yellow
try {
    $body = @{
        portfolio_id = $portfolioId
        symbol = "AAPL"
        side = "BUY"
        type = "MARKET"
        quantity = 10
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/orders" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✅ 订单创建成功: ID=$($response.id), 符号=$($response.symbol)" -ForegroundColor Green
} catch {
    Write-Host "❌ 创建订单失败: $_" -ForegroundColor Red
}

# Test 5: Get orders
Write-Host "`n[5] 测试获取订单列表..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/orders?portfolio_id=$portfolioId" -Method Get
    Write-Host "✅ 获取订单列表成功: 共 $($response.Count) 个订单" -ForegroundColor Green
} catch {
    Write-Host "❌ 获取订单列表失败: $_" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 50) -ForegroundColor Gray
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "`n访问 http://localhost:8000/docs 进行更多测试" -ForegroundColor Cyan
