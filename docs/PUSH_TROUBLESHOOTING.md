# GitHub 推送故障排除

## 当前状态

- ✅ 远程仓库已配置: `https://github.com/indamices/TradeOpenBB.git`
- ✅ 分支已重命名为 `main`
- ⚠️ 推送时遇到连接问题

## 解决方案

### 方案 1: 手动推送（推荐）

直接在终端运行：
```powershell
git push -u origin main
```

如果提示需要身份验证，使用 Personal Access Token。

### 方案 2: 使用 Personal Access Token

#### 步骤 1: 生成 Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 输入名称（如：`TradeOpenBB Push`）
4. 选择过期时间（建议：90 days 或 No expiration）
5. **重要**: 勾选 `repo` 权限
6. 点击 "Generate token"
7. **立即复制 token**（只显示一次）

#### 步骤 2: 使用 Token 推送

推送时：
- **用户名**: 你的 GitHub 用户名（`indamices`）
- **密码**: 粘贴刚才复制的 Personal Access Token

或者配置 Git 凭据：
```powershell
git config --global credential.helper wincred
```

### 方案 3: 使用 SSH（推荐用于长期使用）

#### 步骤 1: 生成 SSH 密钥

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
```

按回车使用默认路径，设置密码（可选）。

#### 步骤 2: 添加 SSH 密钥到 GitHub

1. 复制公钥内容：
   ```powershell
   cat ~/.ssh/id_ed25519.pub
   ```

2. 访问 https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥内容
5. 点击 "Add SSH key"

#### 步骤 3: 更改远程 URL 为 SSH

```powershell
git remote set-url origin git@github.com:indamices/TradeOpenBB.git
git push -u origin main
```

### 方案 4: 使用 GitHub CLI

#### 安装 GitHub CLI

```powershell
# 使用 winget
winget install --id GitHub.cli

# 或使用 Chocolatey
choco install gh
```

#### 登录并推送

```powershell
gh auth login
git push -u origin main
```

## 验证推送

推送成功后，访问：
https://github.com/indamices/TradeOpenBB

应该能看到所有文件。

## 常见错误

### 错误 1: "fatal: unable to access"

**原因**: 网络连接问题或需要身份验证

**解决**: 
- 检查网络连接
- 使用 Personal Access Token
- 配置代理（如果使用）

### 错误 2: "remote: Support for password authentication was removed"

**原因**: GitHub 不再支持密码推送

**解决**: 使用 Personal Access Token

### 错误 3: "Permission denied"

**原因**: 没有推送权限或身份验证失败

**解决**: 
- 检查仓库权限
- 使用正确的 Personal Access Token
- 确保 token 有 `repo` 权限

## 快速命令

```powershell
# 检查远程仓库
git remote -v

# 检查当前分支
git branch

# 推送代码
git push -u origin main

# 查看推送状态
git status
```

## 需要帮助？

如果仍然遇到问题：
1. 检查网络连接
2. 确认 GitHub 账户权限
3. 查看 Git 错误信息
4. 参考 GitHub 官方文档: https://docs.github.com/en/get-started/getting-started-with-git
