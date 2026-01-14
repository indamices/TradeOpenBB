# 推送到 GitHub 指南

## 当前状态

代码已提交到本地仓库，但推送失败（网络连接问题）。

## 已提交的更改

- ✅ 测试文件已创建：
  - `backend/tests/test_openbb_service.py`
  - `backend/tests/test_backtest_engine.py`
  - `backend/tests/test_ai_service_factory.py`
- ✅ 辅助脚本已创建
- ✅ 文档已更新

## 推送方法

### 方法 1: 重试推送（推荐）

如果网络问题已解决，直接运行：

```powershell
git push origin main
```

### 方法 2: 使用 SSH（如果已配置）

```powershell
# 检查是否已配置 SSH
git remote set-url origin git@github.com:indamices/TradeOpenBB.git
git push origin main
```

### 方法 3: 使用 GitHub Desktop

1. 打开 GitHub Desktop
2. 选择仓库
3. 点击 "Push origin" 按钮

### 方法 4: 使用 GitHub CLI

```powershell
# 安装 GitHub CLI (如果未安装)
# winget install GitHub.cli

# 推送
gh repo sync
```

### 方法 5: 配置代理（如果需要）

```powershell
# 如果使用代理
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080

# 推送
git push origin main
```

## 推送后

推送成功后，GitHub Actions 会自动：

1. ✅ 检测到新的提交
2. ✅ 运行测试套件
3. ✅ 生成覆盖率报告
4. ✅ 在 "Actions" 标签页显示结果

## 查看测试结果

推送成功后，访问：
- https://github.com/indamices/TradeOpenBB/actions

## 当前提交信息

```
commit 9399781
Add test files for OpenBB service, Backtest engine, and AI service factory
```

## 如果推送持续失败

可以考虑：
1. 检查网络连接
2. 检查防火墙设置
3. 使用 VPN（如果需要）
4. 稍后重试
