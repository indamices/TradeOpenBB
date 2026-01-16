# 简化的本地测试启动脚本
$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TradeOpenBB 本地测试启动" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Python
Write-Host "[1/7] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    exit 1
}

# 进入 backend 目录
$BackendDir = Join-Path $PSScriptRoot "..\backend"
Set-Location $BackendDir

# 检查/创建虚拟环境
Write-Host "`n[2/7] 设置虚拟环境..." -ForegroundColor Yellow
$venvPath = "venv"
$venvActivate = "venv\Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "  创建虚拟环境..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "  ✓ 虚拟环境已创建" -ForegroundColor Green
} else {
    Write-Host "  ✓ 虚拟环境已存在" -ForegroundColor Green
}

# 激活虚拟环境
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Host "  ✗ 无法激活虚拟环境" -ForegroundColor Red
    exit 1
}

# 升级 pip
Write-Host "`n[3/7] 升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Host "  ✓ pip 已升级" -ForegroundColor Green

# 安装依赖
Write-Host "`n[4/7] 安装依赖（这可能需要几分钟）..." -ForegroundColor Yellow
Write-Host "  使用清华大学镜像源加速..." -ForegroundColor Gray
try {
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green
} catch {
    Write-Host "  尝试使用默认源..." -ForegroundColor Gray
    pip install -r requirements.txt --quiet
    Write-Host "  ✓ 依赖安装完成" -ForegroundColor Green
}

# 验证关键依赖
Write-Host "`n[5/7] 验证关键依赖..." -ForegroundColor Yellow
$deps = @("fastapi", "sqlalchemy", "cryptography", "uvicorn")
$allOk = $true
foreach ($dep in $deps) {
    $result = python -c "import $dep" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $dep" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dep" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host "`n  ✗ 关键依赖验证失败" -ForegroundColor Red
    exit 1
}

# 生成加密密钥
Write-Host "`n[6/7] 生成加密密钥..." -ForegroundColor Yellow
$keyFile = "..\generate_encryption_key.py"
if (Test-Path $keyFile) {
    $keyOutput = python $keyFile 2>&1
    $encryptionKey = ($keyOutput | Select-String -Pattern "^[A-Za-z0-9+/=]{40,}$" | Select-Object -Last 1).Line
    if (-not $encryptionKey) {
        # 尝试直接生成
        $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>&1
        $encryptionKey = $encryptionKey.Trim()
    }
} else {
    $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>&1
    $encryptionKey = $encryptionKey.Trim()
}

if ($encryptionKey -and $encryptionKey.Length -gt 40) {
    Write-Host "  ✓ 加密密钥已生成" -ForegroundColor Green
} else {
    Write-Host "  ! 使用临时密钥" -ForegroundColor Yellow
    $encryptionKey = "temp-key-" + [System.Guid]::NewGuid().ToString()
}

# 创建 .env 文件
Write-Host "`n[7/7] 配置环境变量..." -ForegroundColor Yellow
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    $envContent = @"
DATABASE_URL=sqlite:///./smartquant.db
ENCRYPTION_KEY=$encryptionKey
"@
    $envContent | Out-File -FilePath $envFile -Encoding utf8 -NoNewline
    Write-Host "  ✓ .env 文件已创建" -ForegroundColor Green
    Write-Host "`n  提示: 如需添加 AI API Keys，请编辑 $envFile" -ForegroundColor Gray
} else {
    Write-Host "  ✓ .env 文件已存在" -ForegroundColor Green
}

# 初始化数据库
Write-Host "`n初始化数据库..." -ForegroundColor Yellow
try {
    python -c "from database import init_db; init_db()" 2>&1 | Out-Null
    Write-Host "  ✓ 数据库初始化完成" -ForegroundColor Green
} catch {
    Write-Host "  ! 数据库将在首次启动时自动初始化" -ForegroundColor Yellow
}

# 启动服务器
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  服务器启动中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n  API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  健康检查: http://localhost:8000/" -ForegroundColor Cyan
Write-Host "  API 端点: http://localhost:8000/api/..." -ForegroundColor Cyan
Write-Host "`n  按 Ctrl+C 停止服务器`n" -ForegroundColor Yellow

uvicorn main:app --reload --host 0.0.0.0 --port 8000
