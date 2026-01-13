# SmartQuant 快速启动指南

## 环境变量已配置

✅ 后端环境变量文件已创建: `backend/.env`
✅ 前端环境变量文件已创建: `.env.local`

## 需要完成的步骤

### 1. 生成加密密钥

运行以下命令生成加密密钥：

```bash
python generate_key.py
```

或者手动安装 cryptography 后运行：

```bash
pip install cryptography
python generate_key.py
```

将生成的密钥添加到 `backend/.env` 文件的 `ENCRYPTION_KEY=` 后面。

### 2. 安装后端依赖

由于 pip 可能有问题，建议使用以下方法之一：

**方法 A: 使用 PowerShell 脚本（推荐）**
```powershell
.\start_backend.ps1
```
脚本会自动创建虚拟环境并安装依赖。

**方法 B: 手动安装**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pandas numpy yfinance requests python-dotenv cryptography cachetools
```

### 3. 启动数据库

**选项 A: 使用 Docker**
```bash
docker-compose up -d db
```

**选项 B: 本地 PostgreSQL**
确保 PostgreSQL 已安装并运行，数据库和用户已创建。

### 4. 启动服务

**快速启动（同时启动前后端）:**
```powershell
.\start_all.ps1
```

**分别启动:**

后端:
```powershell
.\start_backend.ps1
```

前端:
```powershell
.\start_frontend.ps1
```

或手动启动:

后端:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

前端:
```bash
npm install
npm run dev
```

## 访问应用

- 后端 API: http://localhost:8000
- 前端界面: http://localhost:5173
- API 文档: http://localhost:8000/docs

## 首次使用

1. 访问前端界面
2. 进入 "AI Settings" 页面
3. 添加 AI 模型配置（Gemini、OpenAI 或 Claude）
4. 开始使用策略生成功能

## 故障排除

如果遇到问题，请查看 `SETUP.md` 获取详细说明。
