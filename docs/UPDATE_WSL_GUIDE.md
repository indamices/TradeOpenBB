# WSL 更新指南

## 🔧 更新 WSL 的步骤

### 方法 1: 使用 PowerShell（推荐）

1. **以管理员身份打开 PowerShell**
   - 右键点击"开始"菜单
   - 选择"Windows PowerShell (管理员)" 或 "终端 (管理员)"

2. **运行更新命令**
   ```powershell
   wsl --update
   ```

3. **等待更新完成**
   - 这可能需要几分钟时间
   - 会显示下载和安装进度

4. **验证更新**
   ```powershell
   wsl --version
   wsl --status
   ```

### 方法 2: 使用脚本

运行项目根目录下的更新脚本：
```powershell
.\update_wsl.ps1
```

**注意**: 如果脚本提示需要管理员权限，请以管理员身份运行 PowerShell。

## ✅ 更新后验证

更新完成后，检查 WSL 版本：
```powershell
wsl --version
```

应该显示类似：
```
WSL version: 2.x.x.x
Kernel version: 5.xx.x
```

## 🐳 更新后启动 Docker

1. **重启 Docker Desktop**
   - 完全关闭 Docker Desktop
   - 重新打开 Docker Desktop
   - 等待 Docker 引擎完全启动

2. **验证 Docker 可用**
   ```powershell
   docker --version
   docker info
   ```

3. **启动服务**
   ```powershell
   .\start_docker.ps1
   ```

## ⚠️ 常见问题

### 问题 1: 更新命令需要管理员权限

**解决方案**: 以管理员身份运行 PowerShell

### 问题 2: 更新失败或超时

**解决方案**:
1. 检查网络连接
2. 重启电脑后重试
3. 手动下载 WSL 更新包（如果可用）

### 问题 3: Docker 仍然提示 WSL 版本过旧

**解决方案**:
1. 完全重启 Docker Desktop
2. 重启电脑
3. 检查 WSL 版本是否真的更新了：`wsl --version`

## 📝 手动更新步骤（如果自动更新失败）

1. 打开 Microsoft Store
2. 搜索 "Windows Subsystem for Linux"
3. 点击"更新"或"获取更新"

## 🎯 下一步

更新 WSL 后：
1. ✅ 重启 Docker Desktop
2. ✅ 运行 `.\start_docker.ps1` 启动服务
3. ✅ 验证服务是否正常运行
