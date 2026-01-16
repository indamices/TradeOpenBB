# 诊断404错误脚本
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  404 错误诊断" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查后端API
Write-Host "[1] 检查后端API端点..." -ForegroundColor Yellow
$endpoints = @(
    "/api/ai-models",
    "/api/strategies",
    "/api/portfolios",
    "/api/market/overview"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000$endpoint" -UseBasicParsing -TimeoutSec 3
        Write-Host "  ✓ $endpoint - 状态码: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "N/A" }
        Write-Host "  ✗ $endpoint - 状态码: $statusCode" -ForegroundColor Red
    }
}

# 检查前端资源
Write-Host "`n[2] 检查前端资源..." -ForegroundColor Yellow
$frontendResources = @(
    "http://localhost:3000/",
    "http://localhost:3000/index.css",
    "http://localhost:3000/index.tsx"
)

foreach ($resource in $frontendResources) {
    try {
        $response = Invoke-WebRequest -Uri $resource -UseBasicParsing -TimeoutSec 3
        Write-Host "  ✓ $resource - 状态码: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "N/A" }
        Write-Host "  ✗ $resource - 状态码: $statusCode" -ForegroundColor Red
    }
}

# 检查环境变量
Write-Host "`n[3] 检查环境变量..." -ForegroundColor Yellow
if (Test-Path ".env.local") {
    $envContent = Get-Content ".env.local"
    Write-Host "  ✓ .env.local 文件存在" -ForegroundColor Green
    foreach ($line in $envContent) {
        if ($line -match "VITE_API_BASE_URL") {
            Write-Host "    $line" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ✗ .env.local 文件不存在" -ForegroundColor Red
    Write-Host "    创建 .env.local 文件..." -ForegroundColor Yellow
    "VITE_API_BASE_URL=http://localhost:8000" | Out-File -FilePath ".env.local" -Encoding utf8
    Write-Host "    ✓ 已创建" -ForegroundColor Green
}

Write-Host "`n[4] 建议检查项:" -ForegroundColor Yellow
Write-Host "  1. 打开浏览器开发者工具 (F12)" -ForegroundColor White
Write-Host "  2. 查看 Console 标签中的错误信息" -ForegroundColor White
Write-Host "  3. 查看 Network 标签，找到404的请求" -ForegroundColor White
Write-Host "  4. 检查404请求的完整URL" -ForegroundColor White
Write-Host "`n  如果是API请求404，检查:" -ForegroundColor Cyan
Write-Host "    - API端点路径是否正确" -ForegroundColor Gray
Write-Host "    - VITE_API_BASE_URL 是否正确" -ForegroundColor Gray
Write-Host "`n  如果是静态资源404，检查:" -ForegroundColor Cyan
Write-Host "    - 文件路径是否正确" -ForegroundColor Gray
Write-Host "    - Vite开发服务器是否正常运行" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
