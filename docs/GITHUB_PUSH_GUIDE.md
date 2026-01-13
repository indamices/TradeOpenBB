# 推送到 GitHub 指南

## 情况 1: 你已经有 GitHub 仓库

如果你已经在 GitHub 上创建了仓库，请提供仓库 URL，然后运行：

```powershell
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

## 情况 2: 你还没有创建 GitHub 仓库

### 步骤 1: 在 GitHub 创建新仓库

1. 访问 https://github.com/new
2. 输入仓库名称（例如：`TradeOpenBB`）
3. **重要**: 
   - ✅ 选择 "Public" 或 "Private"
   - ❌ **不要**勾选 "Initialize this repository with a README"
   - ❌ **不要**添加 .gitignore 或 license
4. 点击 "Create repository"

### 步骤 2: 复制仓库 URL

创建后，GitHub 会显示仓库 URL，格式：
```
https://github.com/你的用户名/TradeOpenBB.git
```

### 步骤 3: 添加远程仓库并推送

运行以下命令（替换为你的实际 URL）：

```powershell
git remote add origin https://github.com/你的用户名/TradeOpenBB.git
git branch -M main
git push -u origin main
```

## 完整命令示例

假设你的 GitHub 用户名是 `yourusername`，仓库名是 `TradeOpenBB`：

```powershell
# 添加远程仓库
git remote add origin https://github.com/yourusername/TradeOpenBB.git

# 将分支重命名为 main（如果当前是 master）
git branch -M main

# 推送到 GitHub
git push -u origin main
```

## 验证推送

推送成功后，访问你的 GitHub 仓库页面，应该能看到所有文件。

## 常见问题

### 问题 1: 认证失败

如果提示需要认证，使用以下方法之一：

**方法 1: 使用 Personal Access Token**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：`repo`
4. 生成并复制 token
5. 推送时使用 token 作为密码

**方法 2: 使用 GitHub CLI**
```powershell
gh auth login
```

### 问题 2: 分支名称不匹配

如果 GitHub 仓库使用 `main` 分支，但本地是 `master`：
```powershell
git branch -M main
git push -u origin main
```

### 问题 3: 远程仓库已存在内容

如果远程仓库已有内容，需要先拉取：
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```
