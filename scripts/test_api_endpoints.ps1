# ============================================================================
# API 端点测试脚本
# 用于测试后端 API 功能
# ============================================================================

$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:8000"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Test {
    param([string]$Name)
    Write-ColorOutput "`n[测试] $Name" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[✓] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[✗] $Message" "Red"
}

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )
    
    $url = "$baseUrl$Endpoint"
    $headers = @{
        "Content-Type" = "application/json"
    }
    foreach ($key in $Headers.Keys) {
        $headers[$key] = $Headers[$key]
    }
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -ErrorAction Stop
        } else {
            $jsonBody = if ($Body) { $Body | ConvertTo-Json -Depth 10 } else { "{}" }
            $response = Invoke-RestMethod -Uri $url -Method $Method -Headers $headers -Body $jsonBody -ErrorAction Stop
        }
        return @{Success=$true; Response=$response}
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = $_.Exception.Message
        return @{Success=$false; StatusCode=$statusCode; Error=$errorMsg}
    }
}

Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "  TradeOpenBB API 端点测试" "Cyan"
Write-ColorOutput "========================================`n" "Cyan"

# 检查服务器是否运行
Write-Test "检查服务器连接"
$healthCheck = Test-Endpoint -Method "GET" -Endpoint "/"
if ($healthCheck.Success) {
    Write-Success "服务器连接正常"
} else {
    Write-Error "无法连接到服务器: $baseUrl"
    Write-ColorOutput "请先运行 setup_and_test_local.ps1 启动服务器" "Yellow"
    exit 1
}

# 测试 1: 获取 API 文档
Write-Test "获取 API 文档"
$docsCheck = Test-Endpoint -Method "GET" -Endpoint "/docs"
if ($docsCheck.Success) {
    Write-Success "API 文档可访问"
} else {
    Write-Error "无法访问 API 文档"
}

# 测试 2: 获取投资组合列表
Write-Test "获取投资组合列表"
$portfolios = Test-Endpoint -Method "GET" -Endpoint "/api/portfolios"
if ($portfolios.Success) {
    Write-Success "获取投资组合成功"
    Write-ColorOutput "  投资组合数量: $($portfolios.Response.Count)" "Gray"
} else {
    Write-Error "获取投资组合失败: $($portfolios.Error)"
}

# 测试 3: 创建投资组合
Write-Test "创建测试投资组合"
$newPortfolio = @{
    name = "测试投资组合"
    initial_cash = 100000.0
}
$createPortfolio = Test-Endpoint -Method "POST" -Endpoint "/api/portfolios" -Body $newPortfolio
if ($createPortfolio.Success) {
    Write-Success "创建投资组合成功"
    $portfolioId = $createPortfolio.Response.id
    Write-ColorOutput "  投资组合 ID: $portfolioId" "Gray"
} else {
    Write-Error "创建投资组合失败: $($createPortfolio.Error)"
    $portfolioId = 1  # 使用默认 ID
}

# 测试 4: 获取 AI 模型列表
Write-Test "获取 AI 模型列表"
$models = Test-Endpoint -Method "GET" -Endpoint "/api/ai/models"
if ($models.Success) {
    Write-Success "获取 AI 模型列表成功"
    Write-ColorOutput "  模型数量: $($models.Response.Count)" "Gray"
} else {
    Write-Error "获取 AI 模型列表失败: $($models.Error)"
}

# 测试 5: 获取市场概览
Write-Test "获取市场概览"
$marketOverview = Test-Endpoint -Method "GET" -Endpoint "/api/market/overview"
if ($marketOverview.Success) {
    Write-Success "获取市场概览成功"
} else {
    Write-Error "获取市场概览失败: $($marketOverview.Error)"
}

# 测试 6: 测试 AI 聊天（如果有模型）
if ($models.Success -and $models.Response.Count -gt 0) {
    Write-Test "测试 AI 聊天功能"
    $chatRequest = @{
        message = "你好，请介绍一下你自己"
        conversation_id = $null
    }
    $chatResponse = Test-Endpoint -Method "POST" -Endpoint "/api/ai/chat" -Body $chatRequest
    if ($chatResponse.Success) {
        Write-Success "AI 聊天测试成功"
        Write-ColorOutput "  AI 响应: $($chatResponse.Response.message.Substring(0, [Math]::Min(100, $chatResponse.Response.message.Length)))..." "Gray"
    } else {
        Write-Error "AI 聊天测试失败: $($chatResponse.Error)"
    }
} else {
    Write-ColorOutput "[!] 跳过 AI 聊天测试（没有配置的 AI 模型）" "Yellow"
    Write-ColorOutput "   提示: 可以通过前端或 API 添加 AI 模型" "Gray"
}

# 测试 7: 获取实时报价
Write-Test "获取股票实时报价 (AAPL)"
$quote = Test-Endpoint -Method "GET" -Endpoint "/api/market/quote/AAPL"
if ($quote.Success) {
    Write-Success "获取股票报价成功"
    Write-ColorOutput "  股票: $($quote.Response.symbol)" "Gray"
    Write-ColorOutput "  价格: $($quote.Response.price)" "Gray"
} else {
    Write-Error "获取股票报价失败: $($quote.Error)"
}

# 测试 8: 获取会话列表
Write-Test "获取聊天会话列表"
$conversations = Test-Endpoint -Method "GET" -Endpoint "/api/ai/conversations"
if ($conversations.Success) {
    Write-Success "获取会话列表成功"
    Write-ColorOutput "  会话数量: $($conversations.Response.Count)" "Gray"
} else {
    Write-Error "获取会话列表失败: $($conversations.Error)"
}

Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "  测试完成！" "Green"
Write-ColorOutput "========================================`n" "Green"
Write-ColorOutput "访问 http://localhost:8000/docs 查看完整 API 文档" "Cyan"
