# 修复 pip 安装问题

## 问题描述

当前 Python 环境缺少 `tomllib` 模块，导致 pip 无法正常工作。`tomllib` 是 Python 3.11+ 的标准库。

## 解决方案

### 方案 1: 更新 Python 到 3.11+（推荐）

1. 下载并安装 Python 3.11 或更高版本
2. 重新创建虚拟环境：
   ```powershell
   cd backend
   Remove-Item -Recurse -Force venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

### 方案 2: 手动安装 tomllib（临时方案）

如果无法更新 Python，可以尝试：

```powershell
# 安装 tomli（tomllib 的替代品）
pip install tomli
```

然后修改 pip 的兼容性文件（不推荐，可能破坏 pip）

### 方案 3: 使用 conda 环境

```powershell
conda create -n smartquant python=3.11
conda activate smartquant
cd backend
pip install -r requirements.txt
```

### 方案 4: 使用 Docker 运行后端

如果本地环境有问题，可以使用 Docker：

```powershell
docker-compose up --build
```

这会构建并启动所有服务（包括数据库和后端）。

## 临时解决方案：跳过某些依赖

如果只需要基本功能，可以先安装核心包：

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# 安装核心包（不使用 requirements.txt）
python -c "import subprocess; packages=['fastapi','uvicorn','sqlalchemy','pydantic','python-dotenv']; [subprocess.run(['python','-m','pip','install',p]) for p in packages]"
```

## 检查 Python 版本

运行以下命令检查 Python 版本：

```powershell
python --version
python -c "import sys; print(sys.version)"
```

如果版本低于 3.11，建议升级到 3.11 或更高版本。
