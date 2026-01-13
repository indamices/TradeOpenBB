# ✅ 设置完成情况

## 已完成 ✅

### 1. 环境变量配置
- ✅ `backend/.env` - 已创建，包含数据库连接配置
- ✅ `.env.local` - 已创建，包含前端 API 地址配置

### 2. 前端依赖
- ✅ 已运行 `npm install`，所有前端依赖已安装（175 个包）

### 3. 启动脚本
- ✅ `start_backend.ps1` - 后端启动脚本
- ✅ `start_frontend.ps1` - 前端启动脚本
- ✅ `start_all.ps1` - 同时启动前后端
- ✅ `generate_key.py` - 加密密钥生成工具

### 4. 文档
- ✅ `SETUP.md` - 详细设置指南
- ✅ `QUICKSTART.md` - 快速启动指南
- ✅ `README_SETUP.md` - 设置总结

## ⚠️ 需要手动完成

### 1. 生成加密密钥（重要）

由于当前环境的 pip 可能有问题，请手动完成：

**方法 1: 使用 Python 脚本（推荐）**
```powershell
# 先安装 cryptography（如果还没安装）
pip install cryptography

# 然后运行
python generate_key.py
```

**方法 2: 手动生成**
```python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

将生成的密钥添加到 `backend/.env` 文件的 `ENCRYPTION_KEY=` 后面。

### 2. 安装后端依赖

**推荐: 使用虚拟环境**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果遇到 pip 问题，可以尝试：
- 更新 pip: `python -m pip install --upgrade pip`
- 或使用 `python -m pip install` 代替 `pip install`

### 3. 启动数据库

**选项 A: Docker（如果已安装）**
```powershell
docker-compose up -d db
```

**选项 B: 本地 PostgreSQL**
确保 PostgreSQL 已安装并运行，然后创建数据库：
```sql
CREATE DATABASE smartquant_db;
CREATE USER quant_user WITH PASSWORD 'quant_password';
GRANT ALL PRIVILEGES ON DATABASE smartquant_db TO quant_user;
```

### 4. 启动服务

**最简单的方法:**
```powershell
.\start_all.ps1
```

这会打开两个窗口：
- 后端: http://localhost:8000
- 前端: http://localhost:5173

**或分别启动:**

后端:
```powershell
.\start_backend.ps1
```

前端:
```powershell
.\start_frontend.ps1
```

## 🚀 快速启动命令

完成上述步骤后，只需运行：

```powershell
.\start_all.ps1
```

## 📋 验证清单

- [ ] 加密密钥已生成并添加到 `backend/.env`
- [ ] 后端依赖已安装
- [ ] 数据库已启动并配置
- [ ] 后端服务运行在 http://localhost:8000
- [ ] 前端服务运行在 http://localhost:5173
- [ ] 可以访问前端界面
- [ ] 在 AI Settings 页面配置了至少一个 AI 模型

## 🎯 下一步

1. 访问 http://localhost:5173
2. 进入 "AI Settings" 页面
3. 添加 AI 模型配置（需要 API Key）:
   - Gemini: 需要 Google API Key
   - OpenAI: 需要 OpenAI API Key
   - Claude: 需要 Anthropic API Key
4. 开始使用策略生成和回测功能

## 📞 需要帮助？

查看以下文档获取更多信息：
- `SETUP.md` - 详细设置说明
- `QUICKSTART.md` - 快速启动指南
