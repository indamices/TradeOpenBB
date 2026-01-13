# Render 快速部署指南 ⚡

## 🚀 5 分钟快速部署

### 步骤 1: 登录 Render（1 分钟）

1. 访问：**https://render.com**
2. 点击 **"Get Started for Free"** 或 **"Sign In"**
3. 选择 **"Sign in with GitHub"**
4. 授权 Render 访问你的 GitHub

---

### 步骤 2: 创建 Blueprint（2 分钟）

1. 点击右上角 **"New +"** → **"Blueprint"**
2. 如果还没连接 GitHub，点击 **"Connect account"**
3. 在仓库列表中找到：**`indamices/TradeOpenBB`**
4. 点击 **"Connect"** 或 **"Apply"**

**Render 会自动**：
- ✅ 检测 `render.yaml` 配置文件
- ✅ 创建后端服务（`tradeopenbb-backend`）
- ✅ 创建前端服务（`tradeopenbb-frontend`）
- ✅ 开始自动部署

---

### 步骤 3: 等待部署（5-10 分钟）

**部署进度**：
- 🟡 **Deploying** - 正在部署（正常）
- 🟢 **Live** - 部署成功 ✅

**查看进度**：
- 点击服务名称 → **"Logs"** 标签页
- 实时查看构建日志

---

### 步骤 4: 配置环境变量（可选，2 分钟）

#### 后端服务

1. 点击 **`tradeopenbb-backend`** 服务
2. 点击 **"Environment"** 标签页
3. 检查以下变量：

**已自动设置**（无需操作）：
- ✅ `DATABASE_URL` - SQLite（默认）
- ✅ `ENCRYPTION_KEY` - 自动生成

**可选设置**（如果需要）：
- `GEMINI_API_KEY` - 如果使用 Gemini AI
- `API_KEY` - 如果使用外部 API

**设置方法**：
1. 点击 **"Add Environment Variable"**
2. 输入变量名和值
3. 点击 **"Save Changes"**

#### 前端服务

1. 点击 **`tradeopenbb-frontend`** 服务
2. 点击 **"Environment"** 标签页
3. 检查 `VITE_API_BASE_URL`：

**自动设置**（推荐）：
- Render 会自动从后端获取 URL
- 格式：`https://tradeopenbb-backend.onrender.com`

**手动设置**（如果自动设置失败）：
1. 等待后端部署完成
2. 复制后端 URL
3. 添加环境变量：
   - 名称：`VITE_API_BASE_URL`
   - 值：`https://tradeopenbb-backend.onrender.com`

---

### 步骤 5: 验证部署（1 分钟）

#### 检查后端

访问后端 URL（如 `https://tradeopenbb-backend.onrender.com`）

**健康检查**：
```bash
curl https://tradeopenbb-backend.onrender.com/
```

**预期响应**：
```json
{"message": "SmartQuant API", "status": "running"}
```

**API 文档**：
访问：`https://tradeopenbb-backend.onrender.com/docs`

#### 检查前端

访问前端 URL（如 `https://tradeopenbb-frontend.onrender.com`）

**预期结果**：
- ✅ 页面正常加载
- ✅ 可以看到 TradeOpenBB 界面
- ✅ 没有控制台错误

---

## ✅ 部署完成检查清单

### 后端服务
- [ ] 服务状态为 "Live"
- [ ] 健康检查返回成功
- [ ] API 文档可以访问（`/docs`）

### 前端服务
- [ ] 服务状态为 "Live"
- [ ] 前端页面可以正常访问
- [ ] `VITE_API_BASE_URL` 已正确设置

### 功能测试
- [ ] 可以创建投资组合
- [ ] 可以添加持仓
- [ ] API 请求成功（浏览器控制台无错误）

---

## 🔧 常见问题

### 问题 1: 后端无法启动

**解决**：
1. 查看日志：服务 → Logs
2. 检查环境变量是否正确
3. 检查 `DATABASE_URL` 设置

### 问题 2: 前端无法连接后端

**解决**：
1. 检查 `VITE_API_BASE_URL` 环境变量
2. 确保后端服务状态为 "Live"
3. 检查浏览器控制台错误

### 问题 3: 部署时间过长

**正常情况**：
- 首次部署需要 5-10 分钟
- 这是正常的，请耐心等待

---

## 📊 服务 URL

部署完成后，你会得到两个 URL：

1. **后端 API**：
   ```
   https://tradeopenbb-backend.onrender.com
   ```

2. **前端应用**：
   ```
   https://tradeopenbb-frontend.onrender.com
   ```

---

## 🔄 更新应用

当你推送代码到 GitHub 的 `main` 分支时：
- Render 会自动检测更改
- 自动触发重新部署
- 无需手动操作

---

## 💡 提示

1. **免费层限制**：
   - 后端服务 15 分钟无活动后会休眠
   - 首次请求需要 30-60 秒唤醒
   - 这是正常的，不影响功能

2. **环境变量**：
   - 敏感信息使用环境变量
   - 不要硬编码 API Key

3. **监控**：
   - 定期查看日志
   - 监控服务状态

---

## 📚 详细文档

- **完整部署指南**: `RENDER_DEPLOYMENT_GUIDE.md`
- **故障排除**: `DEPLOYMENT.md`
- **Render 官方文档**: https://render.com/docs

---

**部署成功后，你的应用就可以在生产环境使用了！** 🎉
