# ENCRYPTION_KEY 设置指南

## 重要说明

`ENCRYPTION_KEY` 是一个全局加密密钥，用于加密/解密**所有**AI模型的API keys。只需要设置一次，所有模型都会使用这个密钥。

## 步骤 1：生成 ENCRYPTION_KEY

### 方法 1：使用 Python（推荐）

如果你本地有 Python 和 cryptography 模块：

```bash
# 安装 cryptography（如果还没有）
pip install cryptography

# 生成密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

或者使用项目提供的脚本：

```bash
python generate_encryption_key.py
```

### 方法 2：使用在线工具

访问：https://8gwifi.org/fernet.jsp

点击 "Generate Fernet Key" 按钮，复制生成的密钥（44个字符，类似：`gAAAAABl...`）

### 方法 3：在 Render 服务中生成（临时）

1. 进入 Render Dashboard → `tradeopenbb-backend` 服务
2. 在 Environment 标签中，临时设置 `ENCRYPTION_KEY` 为 `generateValue: true`
3. 部署后，在 Environment 标签中查看生成的值
4. **重要**：复制这个值，然后改为手动输入（见步骤2）

## 步骤 2：在 Render Dashboard 中设置

### 详细步骤：

1. **登录 Render Dashboard**
   - 访问：https://dashboard.render.com
   - 登录你的账户

2. **进入后端服务**
   - 在服务列表中找到 `tradeopenbb-backend`
   - 点击进入服务详情页

3. **打开环境变量设置**
   - 在左侧菜单中点击 **"Environment"** 标签
   - 找到 `ENCRYPTION_KEY` 环境变量

4. **设置固定密钥值**
   - 如果 `ENCRYPTION_KEY` 存在且值为 `generateValue: true`：
     - 点击编辑（铅笔图标）
     - 删除 `generateValue: true`
     - 在 "Value" 字段中粘贴你生成的密钥（44个字符）
   - 如果 `ENCRYPTION_KEY` 不存在：
     - 点击 "Add Environment Variable"
     - Key: `ENCRYPTION_KEY`
     - Value: 粘贴你生成的密钥
   
5. **保存设置**
   - 点击 "Save Changes"
   - 系统会自动触发重新部署

## 步骤 3：验证设置

### 检查设置是否正确：

1. **确认密钥格式**
   - 密钥应该是 44 个字符
   - 以 `gAAAAAB` 开头
   - 只包含字母、数字、`-` 和 `_`

2. **测试 API key 加密/解密**
   - 部署完成后，尝试添加一个新的 AI 模型
   - 输入 API key 并保存
   - 如果保存成功，说明加密密钥工作正常

3. **检查现有模型**
   - 如果之前已经有模型，检查它们是否还能正常工作
   - 如果出现解密错误，说明密钥不匹配（需要重新输入 API keys）

## 重要注意事项

### ⚠️ 密钥丢失的后果

如果 `ENCRYPTION_KEY` 丢失或改变：
- **所有已加密的 API keys 将无法解密**
- **需要重新输入所有模型的 API keys**
- **数据库中的加密数据将无法使用**

### ✅ 最佳实践

1. **备份密钥**
   - 将生成的 `ENCRYPTION_KEY` 保存在安全的地方（密码管理器）
   - 不要将密钥提交到代码仓库

2. **固定密钥值**
   - 一旦设置，**永远不要改变**（除非有特殊原因）
   - 确保在 Render Dashboard 中设置为固定值，而不是 `generateValue: true`

3. **多环境管理**
   - 如果有多套环境（开发、测试、生产），每个环境使用不同的密钥
   - 但同一环境内，所有模型共享同一个密钥

## 常见问题

### Q: 我需要为每个模型设置不同的 ENCRYPTION_KEY 吗？
**A:** 不需要。一个 `ENCRYPTION_KEY` 用于加密/解密所有模型的 API keys。

### Q: 如果我不小心删除了 ENCRYPTION_KEY 怎么办？
**A:** 如果密钥丢失，所有已加密的 API keys 将无法解密。你需要：
1. 重新生成一个新的 `ENCRYPTION_KEY`
2. 重新输入所有模型的 API keys

### Q: 我可以更改 ENCRYPTION_KEY 吗？
**A:** 可以，但需要迁移：
1. 解密所有现有的 API keys（使用旧密钥）
2. 设置新的 `ENCRYPTION_KEY`
3. 使用新密钥重新加密所有 API keys

### Q: 密钥会出现在日志中吗？
**A:** 不会。代码中已经确保密钥不会出现在日志中。但为了安全，建议：
- 不要在生产日志中记录 API keys
- 定期检查日志配置

## 完成后的操作

设置完成后：
1. ✅ 等待部署完成（通常 2-5 分钟）
2. ✅ 测试添加一个新的 AI 模型
3. ✅ 验证现有模型是否正常工作
4. ✅ 备份 `ENCRYPTION_KEY` 到安全位置

---

**需要帮助？** 如果遇到问题，请检查：
- Render Dashboard 中的环境变量设置
- 后端服务的部署日志
- API key 的格式是否正确
