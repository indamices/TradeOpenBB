# Render API 连接问题修复

## 问题描述

前端显示 404 错误，请求路径为 `/tradeopenbb-backend/api/...`，说明 `VITE_API_BASE_URL` 配置不正确。

## 问题原因

`render.yaml` 中的 `fromService` 配置可能返回了错误的 URL 格式，导致前端请求路径错误。

## 解决方案

### 方案 1: 在 Render Dashboard 手动设置（推荐）

1. 访问 Render Dashboard
2. 找到 `tradeopenbb-frontend` 服务
3. 点击 "Environment" 标签页
4. 添加或修改环境变量：
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://tradeopenbb-backend.onrender.com`
   - **注意**: 不要包含尾部斜杠 `/`
5. 点击 "Save Changes"
6. 服务会自动重新部署

### 方案 2: 检查后端服务 URL

确保后端服务 URL 正确：
- 后端服务 URL: `https://tradeopenbb-backend.onrender.com`
- 健康检查: `https://tradeopenbb-backend.onrender.com/` 应该返回 `{"message": "SmartQuant API", "status": "running"}`
- API 文档: `https://tradeopenbb-backend.onrender.com/docs`

### 验证

修复后，前端请求应该是：
- ✅ `https://tradeopenbb-backend.onrender.com/api/portfolio?portfolio_id=1`
- ❌ `https://tradeopenbb-frontend.onrender.com/tradeopenbb-backend/api/portfolio?portfolio_id=1`

## 常见问题

### 问题 1: 404 错误
- **原因**: `VITE_API_BASE_URL` 配置错误
- **解决**: 手动设置为完整的后端 URL（不带路径）

### 问题 2: CORS 错误
- **原因**: 后端 CORS 配置未包含前端域名
- **解决**: 检查后端 `main.py` 中的 CORS 配置

### 问题 3: 网络错误
- **原因**: 后端服务未运行或已休眠
- **解决**: 检查后端服务状态，等待服务唤醒（免费层需要 30-60 秒）
