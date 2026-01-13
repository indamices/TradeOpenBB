# 🚀 启动服务指南

## 环境已修复 ✅

所有环境问题已解决：
- ✅ Python/pip 环境修复完成
- ✅ 依赖包已安装
- ✅ 虚拟环境已配置
- ✅ 代码已修复

## 启动步骤

### 1. 启动数据库（必须）

**选项 A: Docker（推荐）**
```powershell
docker-compose up -d db
```

**选项 B: 本地 PostgreSQL**
确保 PostgreSQL 服务正在运行，数据库已创建。

### 2. 启动后端服务

```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

或使用虚拟环境：
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端服务（新终端）

```powershell
npm run dev
```

## 快速启动（一键）

```powershell
.\start_all.ps1
```

## 验证服务

- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs  
- 前端: http://localhost:5173

## 故障排除

如果后端启动失败：
1. 检查数据库连接（最重要！）
2. 确保所有依赖已安装
3. 查看错误日志

如果前端无法连接后端：
1. 检查 `.env.local` 中的 `VITE_API_BASE_URL`
2. 确保后端服务正在运行
3. 检查浏览器控制台错误

## 下一步

1. 访问 http://localhost:5173
2. 进入 "AI Settings" 页面
3. 配置 AI 模型（需要 API Key）
4. 开始使用策略生成功能！
