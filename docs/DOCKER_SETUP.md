# Docker 简化环境设置指南

## 🎯 为什么使用 Docker？

- ✅ **零配置** - 无需安装 Python、PostgreSQL 或任何依赖
- ✅ **一键启动** - 所有服务自动配置和启动
- ✅ **环境隔离** - 避免版本冲突和 DLL 错误
- ✅ **跨平台** - Windows/Mac/Linux 相同体验

## 📋 前置要求

### 1. 安装 Docker Desktop

**Windows:**
1. 下载：https://www.docker.com/products/docker-desktop
2. 安装 Docker Desktop
3. 重启电脑
4. 启动 Docker Desktop（确保它在运行）

**验证安装:**
```powershell
docker --version
docker-compose --version
```

## 🚀 快速启动

### 方法 1: 使用启动脚本（推荐）

```powershell
.\start_docker.ps1
```

### 方法 2: 手动启动

```powershell
docker-compose up --build
```

### 方法 3: 后台运行

```powershell
docker-compose up --build -d
```

## 📊 服务说明

### 当前配置（使用 SQLite）

- **数据库**: SQLite（无需单独服务）
- **后端**: FastAPI (端口 8000)
- **前端**: 本地运行 `npm run dev`

### 切换到 PostgreSQL（可选）

1. 编辑 `docker-compose.yml`
2. 取消注释 `db` 服务
3. 修改 `DATABASE_URL` 为 PostgreSQL
4. 取消注释 `depends_on`

## 🔧 常用命令

### 查看日志
```powershell
docker-compose logs -f backend
```

### 停止服务
```powershell
docker-compose down
```

### 停止并删除数据
```powershell
docker-compose down -v
```

### 重建服务
```powershell
docker-compose up --build
```

### 进入容器
```powershell
docker-compose exec backend bash
```

## 🐛 故障排除

### 问题 1: Docker 未运行
**解决**: 启动 Docker Desktop

### 问题 2: 端口被占用
**解决**: 
```powershell
# 检查端口占用
netstat -ano | findstr :8000

# 停止占用端口的进程或修改 docker-compose.yml 中的端口
```

### 问题 3: 构建失败
**解决**:
```powershell
# 清理并重建
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### 问题 4: 数据库连接错误
**解决**: 
- 如果使用 SQLite，确保 `backend_data` volume 已创建
- 如果使用 PostgreSQL，确保 `db` 服务正在运行

## 📝 环境变量

在 `docker-compose.yml` 中配置：
- `DATABASE_URL` - 数据库连接（SQLite 或 PostgreSQL）
- `API_KEY` - AI 服务 API 密钥（可选）
- `ENCRYPTION_KEY` - 加密密钥（自动生成）

## 🎯 下一步

1. 启动 Docker 服务
2. 运行前端：`npm run dev`
3. 访问 http://localhost:5173
4. 在 AI Settings 配置 AI 模型

## 💡 提示

- SQLite 数据库文件存储在 Docker volume 中
- 使用 `docker-compose down -v` 会删除所有数据
- 开发时可以使用 volume 挂载实现代码热重载
- 生产环境建议使用 PostgreSQL
