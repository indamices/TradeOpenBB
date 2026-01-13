# 简化环境设置指南

## 🎯 问题解决

已完成的优化：
1. ✅ **SQLite 支持** - 无需安装 PostgreSQL
2. ✅ **Docker 优化** - 解决所有依赖问题
3. ✅ **简化依赖** - 可选依赖标记为注释
4. ✅ **启动脚本** - 一键启动服务

## 🚀 快速开始

### 方案 A: Docker（推荐，最简单）

**前提**: 安装 Docker Desktop

```powershell
# 1. 安装 Docker Desktop（如果未安装）
# 下载: https://www.docker.com/products/docker-desktop

# 2. 启动所有服务
.\start_docker.ps1

# 3. 启动前端（新终端）
npm run dev
```

**优势**:
- ✅ 零配置
- ✅ 自动安装所有依赖
- ✅ 解决所有环境问题

### 方案 B: 本地 SQLite（无需 Docker）

```powershell
# 1. 启动后端（使用 SQLite）
.\start_local.ps1

# 2. 启动前端（新终端）
npm run dev
```

**优势**:
- ✅ 无需 Docker
- ✅ 无需 PostgreSQL
- ✅ 快速启动

## 📋 详细步骤

### Docker 方案

1. **安装 Docker Desktop**
   - 下载: https://www.docker.com/products/docker-desktop
   - 安装并重启电脑
   - 启动 Docker Desktop

2. **启动服务**
   ```powershell
   .\start_docker.ps1
   ```

3. **验证**
   - 后端: http://localhost:8000/docs
   - 前端: http://localhost:5173

### 本地 SQLite 方案

1. **配置环境变量**
   ```powershell
   cd backend
   # .env 文件会自动创建，使用 SQLite 默认配置
   ```

2. **启动后端**
   ```powershell
   .\start_local.ps1
   ```

3. **启动前端**
   ```powershell
   npm run dev
   ```

## 🔧 配置说明

### 数据库选择

**SQLite（默认，推荐）**:
- 无需安装数据库服务器
- 零配置
- 适合开发和测试

**PostgreSQL（可选）**:
- 适合生产环境
- 需要 Docker 或本地安装
- 修改 `DATABASE_URL` 即可切换

### 环境变量

创建 `backend/.env`:
```env
# SQLite（默认）
DATABASE_URL=sqlite:///./smartquant.db

# 或 PostgreSQL
# DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

ENCRYPTION_KEY=your_encryption_key
```

## 🐛 故障排除

### 问题 1: 后端无法启动

**Docker 方案**:
```powershell
docker-compose logs backend
```

**本地方案**:
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 问题 2: 网络连接错误

1. 检查后端是否运行: http://localhost:8000
2. 检查前端配置: `.env.local` 中 `VITE_API_BASE_URL`
3. 查看浏览器控制台错误

### 问题 3: 数据库错误

**SQLite**:
- 确保 `backend` 目录有写权限
- 数据库文件会自动创建

**PostgreSQL**:
- 确保数据库服务运行
- 检查连接字符串

## 📚 相关文档

- `DOCKER_SETUP.md` - Docker 详细使用指南
- `QUICK_FIX_NETWORK.md` - 网络问题快速修复
- `README.md` - 项目总体说明

## 💡 推荐流程

1. **首次使用**: Docker 方案（最简单）
2. **开发调试**: 本地 SQLite 方案（更快）
3. **生产部署**: Docker + PostgreSQL

## ✅ 验证清单

- [ ] 后端服务运行: http://localhost:8000/docs
- [ ] 前端服务运行: http://localhost:5173
- [ ] 前端能连接到后端（无网络错误）
- [ ] 数据库初始化成功

## 🎉 完成！

如果所有服务都正常运行，你可以：
1. 访问前端界面
2. 配置 AI 模型（AI Settings）
3. 开始使用交易和策略功能
