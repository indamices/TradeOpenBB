# SmartQuant 项目设置指南

## 前置要求

1. **Python 3.11+** - 已安装
2. **PostgreSQL** - 需要安装并运行
3. **Node.js** - 用于前端开发
4. **Docker** (可选) - 用于运行 PostgreSQL

## 步骤 1: 安装后端依赖

在项目根目录执行：

```bash
cd backend
pip install -r requirements.txt
```

如果遇到问题，可以逐个安装：

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pandas numpy yfinance requests python-dotenv cryptography cachetools
```

**注意**: OpenBB 相关包（openbb-terminal, openai, anthropic, google-genai）可能需要单独安装或稍后安装。

## 步骤 2: 配置环境变量

### 后端环境变量 (backend/.env)

已创建 `backend/.env` 文件，包含：

```
DATABASE_URL=postgresql://quant_user:quant_password@localhost:5432/smartquant_db
ENCRYPTION_KEY=
```

**重要**: 需要生成加密密钥。运行以下命令：

```python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将输出的密钥添加到 `backend/.env` 文件的 `ENCRYPTION_KEY=` 后面。

### 前端环境变量 (.env.local)

已创建 `.env.local` 文件，包含：

```
VITE_API_BASE_URL=http://localhost:8000
```

## 步骤 3: 启动数据库

### 选项 A: 使用 Docker (推荐)

如果已安装 Docker，运行：

```bash
docker-compose up -d db
```

### 选项 B: 本地 PostgreSQL

1. 安装 PostgreSQL
2. 创建数据库：

```sql
CREATE DATABASE smartquant_db;
CREATE USER quant_user WITH PASSWORD 'quant_password';
GRANT ALL PRIVILEGES ON DATABASE smartquant_db TO quant_user;
```

## 步骤 4: 启动后端服务

在 `backend` 目录下运行：

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或者使用 Python 模块方式：

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动。

## 步骤 5: 安装前端依赖并启动

在项目根目录执行：

```bash
npm install
npm run dev
```

前端服务将在 http://localhost:5173 启动（Vite 默认端口）。

## 验证安装

1. 访问 http://localhost:8000 - 应该看到 API 信息
2. 访问 http://localhost:5173 - 应该看到前端界面
3. 在浏览器中打开开发者工具，检查是否有 API 连接错误

## 常见问题

### 1. 数据库连接失败

- 确保 PostgreSQL 正在运行
- 检查 `DATABASE_URL` 配置是否正确
- 确保数据库和用户已创建

### 2. 后端启动失败

- 检查所有依赖是否已安装
- 查看错误日志
- 确保 Python 版本 >= 3.11

### 3. 前端无法连接后端

- 检查 `.env.local` 中的 `VITE_API_BASE_URL` 是否正确
- 确保后端服务正在运行
- 检查 CORS 设置

### 4. OpenBB 相关错误

OpenBB Terminal 可能需要额外的配置。如果遇到问题，可以暂时跳过 OpenBB 功能，使用 yfinance 作为数据源。

## 下一步

1. 在 AI Settings 页面配置 AI 模型（Gemini、OpenAI 或 Claude）
2. 创建测试投资组合
3. 尝试生成策略并运行回测
