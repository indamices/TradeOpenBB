# ============================================================================
# 本地完整测试脚本 - TradeOpenBB Backend
# 功能：设置环境、安装依赖、启动服务器、运行测试
# ============================================================================

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "`n[步骤] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[✓] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[✗] $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[!] $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[i] $Message" "Gray"
}

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "  TradeOpenBB 本地测试环境设置" "Cyan"
Write-ColorOutput "========================================`n" "Cyan"

# ============================================================================
# 步骤 1: 检查 Python 环境
# ============================================================================
Write-Step "1. 检查 Python 环境"

try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python 已安装: $pythonVersion"
    
    # 检查 Python 版本
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Error "需要 Python 3.11 或更高版本，当前版本: $pythonVersion"
            exit 1
        }
    }
} catch {
    Write-Error "未找到 Python，请先安装 Python 3.11+"
    Write-Info "下载地址: https://www.python.org/downloads/"
    exit 1
}

# ============================================================================
# 步骤 2: 创建/激活虚拟环境
# ============================================================================
Write-Step "2. 设置虚拟环境"

$venvPath = Join-Path $BackendDir "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Info "创建虚拟环境..."
    Set-Location $BackendDir
    python -m venv venv
    Write-Success "虚拟环境已创建: $venvPath"
} else {
    Write-Success "虚拟环境已存在"
}

# 激活虚拟环境
Write-Info "激活虚拟环境..."
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Success "虚拟环境已激活"
} else {
    Write-Error "无法激活虚拟环境: $venvActivate"
    exit 1
}

# ============================================================================
# 步骤 3: 升级 pip
# ============================================================================
Write-Step "3. 升级 pip"

try {
    python -m pip install --upgrade pip --quiet
    Write-Success "pip 已升级"
} catch {
    Write-Warning "pip 升级失败，继续使用当前版本"
}

# ============================================================================
# 步骤 4: 安装依赖
# ============================================================================
Write-Step "4. 安装 Python 依赖"

Set-Location $BackendDir

# 检查是否有代理设置
$useProxy = $false
$proxyUrl = Read-Host "是否使用代理安装依赖？(y/n，默认 n)"
if ($proxyUrl -eq "y" -or $proxyUrl -eq "Y") {
    $proxyHost = Read-Host "请输入代理地址 (例如: http://127.0.0.1:7890)"
    $env:HTTP_PROXY = $proxyHost
    $env:HTTPS_PROXY = $proxyHost
    $useProxy = $true
    Write-Info "已设置代理: $proxyHost"
}

# 询问是否使用国内镜像
$useMirror = Read-Host "是否使用国内镜像源加速？(y/n，默认 y)"
$mirrorUrl = ""
if ($useMirror -ne "n" -and $useMirror -ne "N") {
    $mirrorUrl = "https://pypi.tuna.tsinghua.edu.cn/simple"
    Write-Info "使用清华大学镜像源"
}

Write-Info "开始安装依赖（这可能需要几分钟）..."

try {
    if ($mirrorUrl) {
        pip install -r requirements.txt -i $mirrorUrl
    } else {
        pip install -r requirements.txt
    }
    Write-Success "依赖安装完成"
} catch {
    Write-Error "依赖安装失败"
    Write-Info "尝试使用国内镜像源..."
    try {
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        Write-Success "使用镜像源安装成功"
    } catch {
        Write-Error "安装失败，请检查网络连接或手动安装"
        exit 1
    }
}

# ============================================================================
# 步骤 5: 验证关键依赖
# ============================================================================
Write-Step "5. 验证关键依赖"

$dependencies = @(
    @{Name="fastapi"; Test="import fastapi"},
    @{Name="sqlalchemy"; Test="import sqlalchemy"},
    @{Name="cryptography"; Test="import cryptography"},
    @{Name="uvicorn"; Test="import uvicorn"},
    @{Name="openai"; Test="import openai"}
)

$allOk = $true
foreach ($dep in $dependencies) {
    try {
        python -c $dep.Test 2>&1 | Out-Null
        Write-Success "$($dep.Name) ✓"
    } catch {
        Write-Warning "$($dep.Name) ✗ (可选)"
        if ($dep.Name -eq "fastapi" -or $dep.Name -eq "sqlalchemy" -or $dep.Name -eq "cryptography") {
            $allOk = $false
        }
    }
}

if (-not $allOk) {
    Write-Error "关键依赖验证失败，请检查安装"
    exit 1
}

# ============================================================================
# 步骤 6: 生成加密密钥
# ============================================================================
Write-Step "6. 生成加密密钥"

$keyGenScript = Join-Path $ProjectRoot "generate_encryption_key.py"
$encryptionKey = ""

if (Test-Path $keyGenScript) {
    try {
        # 切换到项目根目录运行脚本
        Push-Location $ProjectRoot
        $keyOutput = python $keyGenScript 2>&1
        Pop-Location
        
        # 从输出中提取密钥（通常在最后一行）
        $keyLines = $keyOutput | Where-Object { $_ -match "^[A-Za-z0-9+/=]{40,}$" }
        if ($keyLines) {
            $encryptionKey = ($keyLines | Select-Object -Last 1).Trim()
        } else {
            # 尝试从所有输出中提取
            $allOutput = $keyOutput -join "`n"
            if ($allOutput -match "([A-Za-z0-9+/=]{40,})") {
                $encryptionKey = $matches[1]
            }
        }
        
        if ($encryptionKey) {
            Write-Success "加密密钥已生成"
            Write-Info "密钥: $($encryptionKey.Substring(0, [Math]::Min(20, $encryptionKey.Length)))..."
        } else {
            throw "无法从输出中提取密钥"
        }
    } catch {
        Write-Warning "无法生成密钥，尝试使用 Python 直接生成"
        try {
            $pythonCmd = 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
            $encryptionKey = python -c $pythonCmd 2>&1
            $encryptionKey = $encryptionKey.Trim()
            if ($encryptionKey -and $encryptionKey.Length -gt 40) {
                Write-Success "加密密钥已生成（直接方式）"
            } else {
                throw "密钥格式不正确"
            }
        } catch {
            Write-Warning "无法生成密钥，将使用临时密钥"
            $encryptionKey = "temp-key-" + [System.Guid]::NewGuid().ToString()
        }
    }
} else {
    Write-Warning "未找到密钥生成脚本，尝试直接生成"
    try {
        $pythonCmd = 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
        $encryptionKey = python -c $pythonCmd 2>&1
        $encryptionKey = $encryptionKey.Trim()
        if (-not $encryptionKey -or $encryptionKey.Length -lt 40) {
            throw "密钥生成失败"
        }
        Write-Success "加密密钥已生成"
    } catch {
        Write-Warning "无法生成密钥，将使用临时密钥"
        $encryptionKey = "temp-key-" + [System.Guid]::NewGuid().ToString()
    }
}

# ============================================================================
# 步骤 7: 创建 .env 文件
# ============================================================================
Write-Step "7. 配置环境变量"

$envFile = Join-Path $BackendDir ".env"

if (Test-Path $envFile) {
    Write-Warning ".env 文件已存在"
    $overwrite = Read-Host "是否覆盖现有 .env 文件？(y/n，默认 n)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Info "保留现有 .env 文件"
    } else {
        $createNew = $true
    }
} else {
    $createNew = $true
}

if ($createNew) {
    Write-Info "创建 .env 文件..."
    
    # 询问 API Keys
    Write-ColorOutput "`n--- AI API Keys 配置（可选，可直接按回车跳过）---" "Yellow"
    $openaiKey = Read-Host "OpenAI API Key (可选)"
    $geminiKey = Read-Host "Gemini API Key (可选)"
    
    $envContent = @"
# 数据库配置（SQLite，自动创建）
DATABASE_URL=sqlite:///./smartquant.db

# 加密密钥（用于加密存储 AI API keys）
ENCRYPTION_KEY=$encryptionKey

# AI API Keys（可选，可在运行时通过前端添加）
"@
    
    if ($openaiKey) {
        $envContent += "`nAPI_KEY=$openaiKey"
    }
    
    if ($geminiKey) {
        $envContent += "`nGEMINI_API_KEY=$geminiKey"
    }
    
    $envContent | Out-File -FilePath $envFile -Encoding utf8 -NoNewline
    Write-Success ".env 文件已创建: $envFile"
}

# ============================================================================
# 步骤 8: 初始化数据库
# ============================================================================
Write-Step "8. 初始化数据库"

try {
    Set-Location $BackendDir
    python -c "from database import init_db; init_db()" 2>&1 | Out-Null
    Write-Success "数据库初始化完成"
} catch {
    Write-Warning "数据库初始化失败（将在首次启动时自动初始化）"
}

# ============================================================================
# 步骤 9: 启动服务器
# ============================================================================
Write-Step "9. 启动测试服务器"

Write-ColorOutput "`n========================================" "Green"
Write-ColorOutput "  服务器启动中..." "Green"
Write-ColorOutput "========================================`n" "Green"
Write-Info "API 文档: http://localhost:8000/docs"
Write-Info "健康检查: http://localhost:8000/"
Write-Info "API 端点: http://localhost:8000/api/..."
Write-ColorOutput "`n按 Ctrl+C 停止服务器`n" "Yellow"

Set-Location $BackendDir

# 启动服务器
try {
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
} catch {
    Write-Error "服务器启动失败"
    Write-Info "错误信息: $_"
    exit 1
}
