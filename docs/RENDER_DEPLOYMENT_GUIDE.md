# Render 部署完整指南 🚀

本指南将帮助你一步步将 TradeOpenBB 部署到 Render 生产环境。

## 📋 快速开始（5 分钟部署）

### 步骤 1: 登录 Render

1. 访问 **https://render.com**
2. 点击右上角 **"Get Started for Free"** 或 **"Sign In"**
3. 选择 **"Sign in with GitHub"**（推荐，自动连接仓库）
4. 授权 Render 访问你的 GitHub 账户

### 步骤 2: 创建 Blueprint

1. 登录后，点击 **"New +"** 按钮（右上角）
2. 选择 **"Blueprint"**
3. 点击 **"Connect account"** 连接 GitHub（如果还没连接）
4. 在仓库列表中找到 **`indamices/TradeOpenBB`**
5. 点击 **"Connect"** 或 **"Apply"**

### 步骤 3: 自动部署

Render 会自动：
- ✅ 检测 `render.yaml` 配置文件
- ✅ 创建后端服务（`tradeopenbb-backend`）
- ✅ 创建前端服务（`tradeopenbb-frontend`）
- ✅ 开始构建和部署

**等待时间**: 首次部署需要 **5-10 分钟**

---

## 📝 详细步骤说明

### 步骤 1: 准备阶段

#### 1.1 确认 GitHub 仓库

✅ 确保代码已推送到 GitHub：
- 仓库地址：`https://github.com/indamices/TradeOpenBB`
- 分支：`main`
- 包含 `render.yaml` 文件

#### 1.2 检查配置文件

确保以下文件存在：
- ✅ `render.yaml` - Render 部署配置
- ✅ `backend/Dockerfile` - 后端 Docker 配置
- ✅ `backend/requirements.txt` - Python 依赖
- ✅ `package.json` - 前端依赖
- ✅ `vite.config.ts` - 前端构建配置

---

### 步骤 2: 在 Render 创建服务

#### 2.1 访问 Render Dashboard

1. 登录后，你会看到 **Dashboard**
2. 点击 **"New +"** → **"Blueprint"**

#### 2.2 连接 GitHub 仓库

1. 如果还没连接 GitHub：
   - 点击 **"Connect account"**
   - 选择 **"GitHub"**
   - 授权 Render 访问你的仓库
   - 选择 **"All repositories"** 或 **"Only select repositories"**

2. 在仓库列表中找到：
   ```
   indamices / TradeOpenBB
   ```

3. 点击仓库名称或 **"Connect"**

#### 2.3 应用 Blueprint

1. Render 会自动检测 `render.yaml`
2. 你会看到预览：
   - **Backend Service**: `tradeopenbb-backend`
   - **Frontend Service**: `tradeopenbb-frontend`
3. 点击 **"Apply"** 开始部署

---

### 步骤 3: 配置环境变量

#### 3.1 后端服务环境变量

1. 在 Render Dashboard，点击 **`tradeopenbb-backend`** 服务
2. 点击 **"Environment"** 标签页
3. 检查以下变量：

**自动生成的变量**（无需手动设置）：
- ✅ `DATABASE_URL` - 已设置为 SQLite
- ✅ `ENCRYPTION_KEY` - Render 会自动生成

**可选变量**（根据需要设置）：
- `API_KEY` - 如果使用外部金融数据 API
- `GEMINI_API_KEY` - 如果使用 Gemini AI

**设置方法**：
1. 点击 **"Add Environment Variable"**
2. 输入变量名（如 `GEMINI_API_KEY`）
3. 输入变量值
4. 点击 **"Save Changes"**
5. 服务会自动重新部署

#### 3.2 前端服务环境变量

1. 点击 **`tradeopenbb-frontend`** 服务
2. 点击 **"Environment"** 标签页
3. 检查 `VITE_API_BASE_URL`：

**自动设置**（推荐）：
- Render 会自动从后端服务获取 URL
- 格式：`https://tradeopenbb-backend.onrender.com`

**手动设置**（如果自动设置失败）：
1. 等待后端部署完成
2. 复制后端 URL（如 `https://tradeopenbb-backend.onrender.com`）
3. 添加环境变量：
   - 名称：`VITE_API_BASE_URL`
   - 值：`https://tradeopenbb-backend.onrender.com`
4. 点击 **"Save Changes"**

---

### 步骤 4: 监控部署进度

#### 4.1 查看构建日志

1. 在服务页面，点击 **"Logs"** 标签页
2. 实时查看构建和部署日志
3. 常见日志信息：
   ```
   Building Docker image...
   Installing dependencies...
   Starting application...
   Application started successfully
   ```

#### 4.2 检查服务状态

- 🟡 **Deploying** - 正在部署
- 🟢 **Live** - 部署成功，服务运行中
- 🔴 **Failed** - 部署失败（查看日志排查）

**首次部署时间**：
- 后端：5-8 分钟
- 前端：3-5 分钟

---

### 步骤 5: 验证部署

#### 5.1 检查后端服务

**健康检查**：
```bash
curl https://tradeopenbb-backend.onrender.com/
```

**预期响应**：
```json
{
  "message": "SmartQuant API",
  "status": "running"
}
```

**API 文档**：
访问：`https://tradeopenbb-backend.onrender.com/docs`

应该看到 Swagger UI 界面。

#### 5.2 检查前端服务

访问前端 URL（如 `https://tradeopenbb-frontend.onrender.com`）

**预期结果**：
- ✅ 页面正常加载
- ✅ 可以看到 TradeOpenBB 界面
- ✅ 没有控制台错误

#### 5.3 测试功能

1. **创建投资组合**：
   - 在前端界面创建新投资组合
   - 检查是否成功

2. **查看 API 连接**：
   - 打开浏览器开发者工具（F12）
   - 查看 Network 标签页
   - 确认 API 请求成功（状态码 200）

3. **测试 AI 功能**（如果配置了 API Key）：
   - 尝试生成策略
   - 检查是否正常工作

---

## 🔧 常见问题排查

### 问题 1: 后端服务无法启动

**症状**：
- 服务状态显示 "Failed"
- 日志显示错误信息

**排查步骤**：

1. **查看日志**：
   ```
   Render Dashboard → tradeopenbb-backend → Logs
   ```

2. **常见错误**：

   **错误 A: 数据库连接失败**
   ```
   Error: Could not connect to database
   ```
   **解决**：
   - 检查 `DATABASE_URL` 环境变量
   - 如果使用 SQLite，确保路径正确：`sqlite:///./data/smartquant.db`

   **错误 B: 依赖安装失败**
   ```
   ERROR: Could not install packages
   ```
   **解决**：
   - 检查 `backend/requirements.txt` 格式
   - 确保所有依赖版本兼容

   **错误 C: 端口冲突**
   ```
   Address already in use
   ```
   **解决**：
   - Render 会自动处理，无需手动配置
   - 如果仍有问题，检查 Dockerfile

3. **重新部署**：
   - 修复问题后，点击 **"Manual Deploy"** → **"Deploy latest commit"**

---

### 问题 2: 前端无法连接后端

**症状**：
- 前端页面显示 "Network error"
- 浏览器控制台显示 CORS 错误

**排查步骤**：

1. **检查环境变量**：
   ```
   Frontend Service → Environment → VITE_API_BASE_URL
   ```
   - 确保值正确：`https://tradeopenbb-backend.onrender.com`
   - 注意：不要有尾部斜杠 `/`

2. **检查后端 CORS 配置**：
   - 后端已配置允许 `*.render.com` 域名
   - 如果仍有问题，检查后端日志

3. **检查后端服务状态**：
   - 确保后端服务状态为 **"Live"**
   - 访问后端健康检查端点

4. **浏览器控制台检查**：
   - 打开开发者工具（F12）
   - 查看 Console 和 Network 标签页
   - 检查错误信息

---

### 问题 3: 构建失败

**症状**：
- 部署过程中构建失败
- 日志显示构建错误

**排查步骤**：

1. **后端构建失败**：
   - 检查 `backend/Dockerfile` 语法
   - 检查 `backend/requirements.txt` 依赖
   - 查看构建日志中的具体错误

2. **前端构建失败**：
   - 检查 `package.json` 依赖
   - 检查 `vite.config.ts` 配置
   - 确保 Node.js 版本兼容（Render 使用 Node 18+）

3. **常见构建错误**：

   **错误 A: 内存不足**
   ```
   JavaScript heap out of memory
   ```
   **解决**：
   - 这是免费层限制
   - 考虑升级到付费计划
   - 或优化构建配置

   **错误 B: 依赖版本冲突**
   ```
   peer dependency conflict
   ```
   **解决**：
   - 更新 `package.json` 依赖版本
   - 使用 `npm install --legacy-peer-deps`

---

### 问题 4: 服务启动超时

**症状**：
- 服务一直显示 "Deploying"
- 超过 10 分钟仍未完成

**排查步骤**：

1. **检查构建日志**：
   - 查看是否有错误
   - 检查构建进度

2. **可能原因**：
   - 免费层资源限制
   - 构建时间过长
   - 网络问题

3. **解决方案**：
   - 等待更长时间（首次部署可能需要 15 分钟）
   - 检查构建日志
   - 考虑升级到付费计划

---

## 📊 部署后检查清单

### ✅ 后端服务

- [ ] 服务状态为 "Live"
- [ ] 健康检查端点返回成功
- [ ] API 文档可以访问（`/docs`）
- [ ] 环境变量已正确设置
- [ ] 日志中没有错误

### ✅ 前端服务

- [ ] 服务状态为 "Live"
- [ ] 前端页面可以正常访问
- [ ] `VITE_API_BASE_URL` 已正确设置
- [ ] 浏览器控制台没有错误
- [ ] API 请求成功

### ✅ 功能测试

- [ ] 可以创建投资组合
- [ ] 可以添加持仓
- [ ] 可以创建订单
- [ ] AI 功能正常（如果配置了 API Key）
- [ ] 数据持久化正常

---

## 🔄 更新部署

### 自动更新

当你推送代码到 GitHub 的 `main` 分支时：
1. Render 会自动检测更改
2. 自动触发重新部署
3. 部署完成后服务自动更新

### 手动更新

1. 在 Render Dashboard，选择服务
2. 点击 **"Manual Deploy"**
3. 选择 **"Deploy latest commit"**
4. 等待部署完成

---

## 📈 监控和维护

### 查看日志

1. 在服务页面，点击 **"Logs"** 标签页
2. 实时查看服务日志
3. 可以搜索和过滤日志

### 查看指标

Render Dashboard 显示：
- CPU 使用率
- 内存使用率
- 请求数
- 响应时间

### 重启服务

1. 在服务页面，点击 **"Restart"** 按钮
2. 服务会重新启动
3. 通常需要 1-2 分钟

---

## 💰 成本说明

### Render 免费层

**后端服务**：
- ✅ 免费
- ⚠️ 有资源限制（512MB RAM, 0.1 CPU）
- ⚠️ 服务休眠：15 分钟无活动后自动休眠
- ⚠️ 唤醒时间：首次请求需要 30-60 秒

**前端服务**：
- ✅ 完全免费
- ✅ 无休眠限制
- ✅ CDN 加速

**PostgreSQL**（如果使用）：
- ✅ 免费 90 天
- ⚠️ 之后需要付费（$7/月）

### 付费计划

如果需要更好的性能：
- **Starter**: $7/月/服务
  - 512MB RAM, 0.5 CPU
  - 无休眠
  - 更快响应

- **Standard**: $25/月/服务
  - 2GB RAM, 1 CPU
  - 更好的性能

---

## 🎯 最佳实践

### 1. 使用环境变量

- ✅ 敏感信息（API Key）使用环境变量
- ✅ 不要硬编码配置
- ✅ 使用 Render 的环境变量管理

### 2. 监控日志

- ✅ 定期查看日志
- ✅ 设置错误告警（付费计划）
- ✅ 及时发现问题

### 3. 数据库选择

- **测试环境**: SQLite（简单，免费）
- **生产环境**: PostgreSQL（稳定，持久化）

### 4. 版本控制

- ✅ 所有更改通过 Git 提交
- ✅ 使用分支管理（main, dev）
- ✅ 添加有意义的提交信息

---

## 🚀 下一步

部署成功后，你可以：

1. **分享应用**：
   - 将前端 URL 分享给用户
   - 测试真实使用场景

2. **配置自定义域名**（可选）：
   - 在服务设置中添加自定义域名
   - 配置 DNS 记录

3. **设置 CI/CD**：
   - 配置自动测试
   - 自动部署流程

4. **监控和优化**：
   - 监控性能指标
   - 优化响应时间
   - 扩展功能

---

## 📞 获取帮助

- **Render 文档**: https://render.com/docs
- **Render 社区**: https://community.render.com
- **项目 Issues**: https://github.com/indamices/TradeOpenBB/issues

---

**祝部署顺利！** 🎉

如有问题，请查看日志或联系支持。
