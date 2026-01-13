# 云平台部署指南

本指南将帮助你将 TradeOpenBB 项目部署到 Render 云平台。

## 📋 目录

- [前置要求](#前置要求)
- [部署步骤](#部署步骤)
- [数据库选择](#数据库选择)
- [环境变量配置](#环境变量配置)
- [部署后验证](#部署后验证)
- [故障排除](#故障排除)
- [其他平台](#其他平台)

---

## 前置要求

### 1. GitHub 账户
- 如果没有，访问 https://github.com 注册

### 2. Render 账户
- 访问 https://render.com 注册（可使用 GitHub 账户登录）
- 免费层可用

### 3. 代码已推送到 GitHub
- 确保代码已提交到 GitHub 仓库

---

## 部署步骤

### 步骤 1: 准备 GitHub 仓库

#### 1.1 初始化 Git（如果还没有）

```bash
git init
git add .
git commit -m "Initial commit: TradeOpenBB project"
```

#### 1.2 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 输入仓库名称（如 `TradeOpenBB`）
3. **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

#### 1.3 推送代码到 GitHub

```bash
git remote add origin https://github.com/你的用户名/TradeOpenBB.git
git branch -M main
git push -u origin main
```

### 步骤 2: 在 Render 创建服务

#### 2.1 创建 Blueprint

1. 访问 https://render.com
2. 登录你的账户
3. 点击 "New +" → "Blueprint"
4. 点击 "Connect account" 连接 GitHub
5. 选择你的仓库（`TradeOpenBB`）
6. 点击 "Apply"

#### 2.2 Render 自动检测配置

- Render 会自动检测 `render.yaml` 文件
- 会自动创建以下服务：
  - `tradeopenbb-backend` (后端 API)
  - `tradeopenbb-frontend` (前端静态站点)
  - （可选）`tradeopenbb-db` (PostgreSQL 数据库，如果启用)

#### 2.3 等待部署完成

- 首次部署需要 **5-10 分钟**
- 可以在 Render Dashboard 查看构建日志
- 构建完成后，服务会自动启动

---

## 数据库选择

### 选项 1: SQLite（推荐用于测试）

**优点**:
- ✅ 无需额外数据库服务
- ✅ 配置简单
- ✅ 免费

**配置**:
- 在 `render.yaml` 中，`DATABASE_URL` 已设置为 SQLite
- 无需额外配置

**限制**:
- ⚠️ 不适合高并发
- ⚠️ 数据存储在容器内（容器重启可能丢失数据）

### 选项 2: PostgreSQL（推荐用于生产）

**优点**:
- ✅ 生产环境推荐
- ✅ 数据持久化
- ✅ 支持高并发

**配置步骤**:

1. **修改 `render.yaml`**:
   ```yaml
   # 在 backend 服务的 envVars 中，注释掉 SQLite，启用 PostgreSQL:
   - key: DATABASE_URL
     fromDatabase:
       name: tradeopenbb-db
       property: connectionString
   ```

2. **取消注释数据库服务**:
   ```yaml
   databases:
     - name: tradeopenbb-db
       plan: free
       databaseName: smartquant_db
       user: quant_user
   ```

3. **重新部署**:
   - 推送更改到 GitHub
   - Render 会自动重新部署

---

## 环境变量配置

### 必需的环境变量

在 Render Dashboard 中配置以下环境变量：

#### 后端服务 (`tradeopenbb-backend`)

1. **ENCRYPTION_KEY** (自动生成)
   - Render 会自动生成
   - 或手动设置：32 字符的随机字符串

2. **API_KEY** (可选)
   - 如果使用外部 API（如金融数据 API）
   - 在 Environment 标签页手动设置

3. **GEMINI_API_KEY** (可选)
   - 如果使用 Gemini AI
   - 在 Environment 标签页手动设置

#### 前端服务 (`tradeopenbb-frontend`)

1. **VITE_API_BASE_URL** (自动设置)
   - Render 会自动从后端服务获取
   - 格式：`https://tradeopenbb-backend.onrender.com`
   - 如果自动设置失败，手动设置后端 URL

### 配置步骤

1. 在 Render Dashboard 中，选择服务（如 `tradeopenbb-backend`）
2. 点击 "Environment" 标签页
3. 点击 "Add Environment Variable"
4. 输入变量名和值
5. 点击 "Save Changes"
6. 服务会自动重新部署

---

## 部署后验证

### 1. 检查后端服务

#### 健康检查
```bash
curl https://tradeopenbb-backend.onrender.com/
```

应该返回：
```json
{"message": "SmartQuant API", "status": "running"}
```

#### API 文档
访问：`https://tradeopenbb-backend.onrender.com/docs`

应该看到 Swagger UI 文档界面。

### 2. 检查前端服务

访问前端 URL（如 `https://tradeopenbb-frontend.onrender.com`）

应该看到 TradeOpenBB 应用界面。

### 3. 测试 API 连接

在前端界面中：
1. 尝试创建投资组合
2. 检查是否能连接到后端 API
3. 查看浏览器控制台是否有错误

---

## 故障排除

### 问题 1: 后端服务无法启动

**症状**: 服务状态显示 "Failed" 或不断重启

**可能原因**:
- 数据库连接失败
- 环境变量缺失
- 代码错误

**解决方案**:
1. 查看日志：Render Dashboard → 服务 → Logs
2. 检查环境变量是否设置正确
3. 检查 `DATABASE_URL` 是否正确

### 问题 2: 前端无法连接后端

**症状**: 前端显示 "Network error" 或 "Failed to fetch"

**可能原因**:
- `VITE_API_BASE_URL` 未设置或错误
- CORS 配置问题
- 后端服务未运行

**解决方案**:
1. 检查前端环境变量 `VITE_API_BASE_URL`
2. 确保后端服务正在运行
3. 检查浏览器控制台的错误信息
4. 验证后端 CORS 配置包含前端域名

### 问题 3: 数据库连接失败

**症状**: 后端日志显示数据库连接错误

**可能原因**:
- PostgreSQL 服务未启动
- 连接字符串错误
- 数据库权限问题

**解决方案**:
1. 检查 PostgreSQL 服务状态
2. 验证 `DATABASE_URL` 格式
3. 检查数据库用户权限

### 问题 4: 构建失败

**症状**: 部署过程中构建失败

**可能原因**:
- 依赖安装失败
- Dockerfile 错误
- 代码语法错误

**解决方案**:
1. 查看构建日志
2. 检查 `requirements.txt` 和 `package.json`
3. 验证 Dockerfile 语法

### 问题 5: 服务启动超时

**症状**: 服务一直显示 "Deploying"

**可能原因**:
- 构建时间过长
- 资源不足（免费层限制）

**解决方案**:
1. 等待更长时间（首次部署可能需要 10-15 分钟）
2. 检查构建日志
3. 考虑升级到付费计划

---

## 其他平台

### Railway

1. 访问 https://railway.app
2. 点击 "New Project" → "Deploy from GitHub repo"
3. 选择你的仓库
4. Railway 会自动检测并部署

**优点**: 无需配置文件，自动检测项目类型

### Fly.io

1. 安装 Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. 登录: `flyctl auth login`
3. 初始化: `flyctl launch`
4. 部署: `flyctl deploy`

**优点**: 全球部署，低延迟

### Vercel (仅前端) + Render (后端)

1. **前端部署到 Vercel**:
   - 访问 https://vercel.com
   - 导入 GitHub 仓库
   - 自动部署

2. **后端部署到 Render**:
   - 按照本指南部署后端

**优点**: Vercel 对前端优化更好，Render 对后端支持更好

---

## 更新部署

### 自动更新

- 当你推送代码到 GitHub 的 `main` 分支时
- Render 会自动检测并重新部署

### 手动更新

1. 在 Render Dashboard 中，选择服务
2. 点击 "Manual Deploy" → "Deploy latest commit"

---

## 监控和维护

### 查看日志

1. 在 Render Dashboard 中，选择服务
2. 点击 "Logs" 标签页
3. 实时查看服务日志

### 查看指标

- CPU 使用率
- 内存使用率
- 请求数
- 响应时间

### 重启服务

1. 在服务页面，点击 "Restart"
2. 服务会重新启动

---

## 成本估算

### Render 免费层

- **后端服务**: 免费（有资源限制）
- **前端服务**: 免费
- **PostgreSQL**: 免费（90 天试用，之后需要付费）

### 付费计划

- **Starter**: $7/月/服务
- **Standard**: $25/月/服务
- **Pro**: $85/月/服务

---

## 总结

### 快速部署清单

- [ ] 代码已推送到 GitHub
- [ ] 在 Render 创建 Blueprint
- [ ] 等待部署完成
- [ ] 配置环境变量
- [ ] 验证服务运行
- [ ] 测试前端连接后端

### 推荐配置

- **测试环境**: SQLite + 免费层
- **生产环境**: PostgreSQL + Starter 计划

---

## 获取帮助

- Render 文档: https://render.com/docs
- Render 社区: https://community.render.com
- 项目 Issues: 在 GitHub 仓库中创建 Issue

---

**祝部署顺利！** 🚀
