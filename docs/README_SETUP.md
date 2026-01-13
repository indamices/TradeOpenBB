# 设置完成总结

## ✅ 已完成的工作

### 1. 环境变量配置
- ✅ 创建了 `backend/.env` 文件（包含数据库连接配置）
- ✅ 创建了 `.env.local` 文件（包含前端 API 地址）

### 2. 启动脚本
- ✅ 创建了 `start_backend.ps1` - 启动后端服务
- ✅ 创建了 `start_frontend.ps1` - 启动前端服务  
- ✅ 创建了 `start_all.ps1` - 同时启动前后端
- ✅ 创建了 `generate_key.py` - 生成加密密钥

### 3. 文档
- ✅ 创建了 `SETUP.md` - 详细设置指南
- ✅ 创建了 `QUICKSTART.md` - 快速启动指南

## ⚠️ 需要手动完成的步骤

### 1. 生成加密密钥

由于 pip 在当前环境可能有问题，请手动完成：

**选项 A: 如果 cryptography 已安装**
```bash
python generate_key.py
```

**选项 B: 手动生成（临时）**
可以暂时在 `backend/.env` 中使用一个临时密钥，稍后替换：
```
ENCRYPTION_KEY=your-temporary-key-here
```

### 2. 安装后端依赖

**推荐方法: 使用虚拟环境**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果遇到 pip 问题，可以逐个安装核心包：
```powershell
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pandas numpy python-dotenv cryptography
```

### 3. 启动数据库

**如果使用 Docker:**
```bash
docker-compose up -d db
```

**如果使用本地 PostgreSQL:**
确保 PostgreSQL 服务正在运行，并创建数据库：
```sql
CREATE DATABASE smartquant_db;
CREATE USER quant_user WITH PASSWORD 'quant_password';
GRANT ALL PRIVILEGES ON DATABASE smartquant_db TO quant_user;
```

### 4. 启动服务

**最简单的方法:**
```powershell
.\start_all.ps1
```

这会打开两个 PowerShell 窗口，分别运行后端和前端。

## 📝 下一步

1. 生成加密密钥并更新 `backend/.env`
2. 安装后端依赖
3. 启动数据库
4. 运行 `.\start_all.ps1` 启动服务
5. 访问 http://localhost:5173 使用应用
6. 在 AI Settings 页面配置 AI 模型

## 🔍 验证安装

访问以下 URL 验证服务是否正常运行：
- http://localhost:8000 - 后端 API（应显示 JSON 响应）
- http://localhost:8000/docs - API 文档
- http://localhost:5173 - 前端界面

## 📚 更多信息

查看 `SETUP.md` 获取详细的设置说明和故障排除指南。
