# 快速修复网络连接问题

## 问题
前端显示："Network error: Could not connect to server"
后端端口 8000 无响应

## 立即解决方案

### 方案 1: 使用 SQLite 启动后端（最简单）

**步骤**:
1. 确保 `backend/.env` 使用 SQLite：
   ```
   DATABASE_URL=sqlite:///./smartquant.db
   ```

2. 启动后端：
   ```powershell
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. 如果遇到依赖问题，使用 Docker（见下方）

### 方案 2: 使用 Docker（推荐，解决所有问题）

**前提**: 安装 Docker Desktop

**步骤**:
```powershell
.\start_docker.ps1
```

这会自动：
- 构建后端镜像
- 安装所有依赖
- 启动服务
- 检查健康状态

### 方案 3: 临时使用 Mock 数据

如果后端无法启动，可以临时让前端使用 Mock 数据：

1. 修改 `components/Dashboard.tsx`:
   ```typescript
   // 临时使用 MockService
   import { MockService } from '../services/mockStore';
   ```

2. 其他组件类似修改

## 验证修复

1. **检查后端**:
   ```powershell
   curl http://localhost:8000
   # 或
   Invoke-WebRequest http://localhost:8000
   ```

2. **检查前端**:
   - 打开浏览器控制台
   - 查看网络请求
   - 确认能连接到 http://localhost:8000

## 推荐方案

**立即**: 使用 Docker（如果已安装）
**或**: 使用 SQLite + 修复后端启动

查看 `DOCKER_SETUP.md` 获取详细 Docker 使用说明。
