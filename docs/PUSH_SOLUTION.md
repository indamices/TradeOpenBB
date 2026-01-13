# GitHub 推送解决方案

## 当前问题

推送时遇到网络连接错误：
- `Connection was reset`
- `Could not connect to server`

## 解决方案

### 方案 1: 检查网络和防火墙

1. **检查网络连接**
   ```powershell
   ping github.com
   ```

2. **检查防火墙设置**
   - 确保防火墙允许 Git 和 PowerShell 访问网络
   - 临时关闭防火墙测试

3. **检查代理设置**
   ```powershell
   git config --global --get http.proxy
   git config --global --get https.proxy
   ```
   
   如果需要设置代理：
   ```powershell
   git config --global http.proxy http://proxy.example.com:8080
   git config --global https.proxy https://proxy.example.com:8080
   ```

### 方案 2: 使用 GitHub Desktop（推荐）

1. **下载 GitHub Desktop**
   - 访问：https://desktop.github.com
   - 下载并安装

2. **使用 GitHub Desktop 推送**
   - 打开 GitHub Desktop
   - File → Add Local Repository
   - 选择项目目录：`C:\Users\Administrator\online-game\TradeOpenBB`
   - 点击 "Publish repository"
   - 输入仓库名：`TradeOpenBB`
   - 点击 "Publish Repository"

### 方案 3: 使用 GitHub CLI

1. **安装 GitHub CLI**
   ```powershell
   # 使用 winget
   winget install --id GitHub.cli
   
   # 或使用 Chocolatey
   choco install gh
   ```

2. **登录并推送**
   ```powershell
   gh auth login
   git push -u origin main
   ```

### 方案 4: 手动推送（在终端中）

1. **打开新的 PowerShell 窗口**
   - 以管理员身份运行（如果需要）

2. **导航到项目目录**
   ```powershell
   cd C:\Users\Administrator\online-game\TradeOpenBB
   ```

3. **推送代码**
   ```powershell
   git push -u origin main
   ```

4. **如果提示身份验证**
   - 用户名：`indamices`
   - 密码：使用 Personal Access Token
     - 生成 Token：https://github.com/settings/tokens
     - 选择 `repo` 权限

### 方案 5: 使用 SSH（如果 HTTPS 有问题）

1. **生成 SSH 密钥**
   ```powershell
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **添加 SSH 密钥到 GitHub**
   - 复制公钥：`cat ~/.ssh/id_ed25519.pub`
   - 访问：https://github.com/settings/keys
   - 添加新的 SSH key

3. **更改远程 URL**
   ```powershell
   git remote set-url origin git@github.com:indamices/TradeOpenBB.git
   git push -u origin main
   ```

## 当前 Git 配置

已配置：
- ✅ 远程仓库：`https://github.com/indamices/TradeOpenBB.git`
- ✅ 分支：`main`
- ✅ 凭据助手：`wincred`
- ✅ 超时时间：600 秒
- ✅ 缓冲区大小：500MB

## 验证推送

推送成功后，访问：
https://github.com/indamices/TradeOpenBB

应该能看到所有 119 个文件。

## 推荐方案

**最简单的方法**：使用 **GitHub Desktop**
- 图形界面，易于使用
- 自动处理身份验证
- 不需要命令行操作

## 需要帮助？

如果仍然无法推送：
1. 检查网络连接是否正常
2. 尝试使用不同的网络（如手机热点）
3. 联系网络管理员检查防火墙设置
4. 使用 GitHub Desktop 作为替代方案
