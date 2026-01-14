# Render PostgreSQL 数据库配置指南

## 问题说明

在使用 Render PostgreSQL 数据库时，如果遇到以下错误：
```
could not translate host name "dpg-xxxxx-a" to address: Name or service not known
```

这是因为 Render 的 `fromDatabase` 属性默认使用 **internal** 连接字符串（内部主机名），但某些情况下后端服务无法解析该内部主机名。

## 解决方案

### 方法 1：在 Render Dashboard 手动设置 External 连接字符串（推荐）

1. **访问 Render Dashboard**
   - 进入 `tradeopenbb-backend` 服务
   - 点击 "Environment" 标签页

2. **查找 DATABASE_URL 环境变量**
   - 如果已存在，点击编辑
   - 如果不存在，点击 "Add Environment Variable"

3. **设置连接字符串**
   - **Key**: `DATABASE_URL`
   - **Value**: 使用 **External** 连接字符串（包含完整域名）
     ```
     postgresql://quant_user:password@dpg-xxxxx-a.oregon-postgres.render.com/smartquant_db
     ```
   - **注意**: 
     - 使用 External 连接字符串（包含 `.oregon-postgres.render.com` 完整域名）
     - 不要使用 Internal 连接字符串（只有 `-a` 后缀的主机名）

4. **保存更改**
   - 点击 "Save Changes"
   - 服务会自动重新部署（等待 2-3 分钟）

### 方法 2：检查数据库服务状态

1. **确认数据库服务已启动**
   - 在 Render Dashboard 中，检查 `tradeopenbb-db` 服务
   - 确保状态为 "Available"

2. **获取连接字符串**
   - 进入 `tradeopenbb-db` 服务
   - 在 "Connections" 标签页
   - 复制 **External Connection String**
   - 在 `tradeopenbb-backend` 服务的 Environment 中设置 `DATABASE_URL`

## 验证连接

配置完成后，可以通过以下方式验证：

1. **检查服务日志**
   - 在 Render Dashboard 中查看 `tradeopenbb-backend` 服务的日志
   - 应该看到 "Database initialized successfully" 消息
   - 不应该看到数据库连接错误

2. **测试 API**
   - 访问后端 API：`https://tradeopenbb-backend.onrender.com/`
   - 应该返回 `{"message": "SmartQuant API", "status": "running"}`

3. **测试数据库操作**
   - 在前端添加 AI 模型
   - 应该可以成功保存，不会出现连接错误

## 常见问题

### Q: 为什么不能使用 Internal 连接字符串？
A: Internal 连接字符串使用内部主机名（如 `dpg-xxxxx-a`），只有在 Render 内部网络中才能解析。如果后端服务无法解析该主机名，需要使用 External 连接字符串（包含完整域名）。

### Q: 如何获取 External 连接字符串？
A: 在 Render Dashboard 中，进入数据库服务 → "Connections" 标签页 → 复制 "External Connection String"。

### Q: 密码在哪里？
A: Render 会自动生成数据库密码。在数据库服务的 "Connections" 标签页可以查看完整的连接字符串（包含密码）。

### Q: 连接字符串格式是什么？
A: PostgreSQL 连接字符串格式：
```
postgresql://用户名:密码@主机名:端口/数据库名
```
例如：
```
postgresql://quant_user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/smartquant_db
```

## 注意事项

1. **安全性**：连接字符串包含密码，请妥善保管
2. **持久化**：使用 PostgreSQL 后，数据会持久化存储，即使容器重新部署也不会丢失
3. **区域**：确保数据库服务和应用服务在同一区域（如 Oregon）以获得最佳性能
