# Fixed backend startup script
# This script tries multiple methods to start the backend

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  启动后端服务（修复版）" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Method 1: Try direct start
Write-Host "[方法 1] 尝试直接启动..." -ForegroundColor Yellow
cd backend

# Fix .env if needed
if (-not (Test-Path ".env") -or (Get-Content ".env" | Select-String "postgresql")) {
    Write-Host "修复 .env 文件..." -ForegroundColor Gray
    @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@ | Out-File -FilePath ".env" -Encoding utf8 -Force
}

# Initialize database
Write-Host "初始化数据库..." -ForegroundColor Gray
$initCmd = 'import sys; sys.path.insert(0, "."); from database import init_db; init_db()'
python -c $initCmd 2>&1 | Out-Null

# Try to start
Write-Host "启动服务..." -ForegroundColor Gray
try {
    $process = Start-Process python -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -PassThru -NoNewWindow
    Start-Sleep -Seconds 3
    
    # Check if running
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 2 -UseBasicParsing
        Write-Host "`n✅✅✅ 服务启动成功！✅✅✅" -ForegroundColor Green
        Write-Host "`n访问地址:" -ForegroundColor Cyan
        Write-Host "  http://localhost:8000" -ForegroundColor White
        Write-Host "  http://localhost:8000/docs" -ForegroundColor White
        Write-Host "`n按 Ctrl+C 停止服务" -ForegroundColor Yellow
        $process.WaitForExit()
    } catch {
        Write-Host "`n⚠️  服务启动但未响应" -ForegroundColor Yellow
        Write-Host "   可能遇到 pydantic-core DLL 问题" -ForegroundColor Gray
        Write-Host "`n建议使用 Docker:" -ForegroundColor Cyan
        Write-Host "  .\start_docker.ps1" -ForegroundColor White
        Write-Host "`n或查看 FINAL_FIX_SOLUTION.md" -ForegroundColor Gray
    }
} catch {
    Write-Host "`n❌ 启动失败" -ForegroundColor Red
    Write-Host "`n错误信息:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`n建议解决方案:" -ForegroundColor Cyan
    Write-Host "  1. 使用 Docker: .\start_docker.ps1" -ForegroundColor White
    Write-Host "  2. 查看 FINAL_FIX_SOLUTION.md" -ForegroundColor White
    Write-Host "  3. 安装 Visual C++ Redistributable" -ForegroundColor White
}

cd ..
