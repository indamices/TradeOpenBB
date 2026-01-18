# Futu OpenAPI 设置指南

## 概述

Futu OpenAPI 是一个可选的数据源，支持港股、美股和A股市场数据，特别是资金流向等高级数据。

**重要**：Futu 功能需要本地安装并运行 OpenD 客户端。

---

## 前置要求

### 1. 安装 OpenD 客户端

**下载地址**：https://openapi.futunn.com/download

**安装步骤**：
1. 下载适合您操作系统的 OpenD 客户端
2. 安装并启动 OpenD
3. 在 OpenD 中登录您的富途账户

### 2. 确认 OpenD 运行状态

- **默认端口**：`127.0.0.1:11111`
- **验证方法**：检查 OpenD 客户端是否显示"已连接"状态

---

## 安装 Python SDK

### 方式 1: 通过 requirements.txt（推荐）

Futu Python SDK 已经包含在 `requirements.txt` 中：

```bash
cd backend
pip install -r requirements.txt
```

### 方式 2: 手动安装

```bash
pip install futu==0.0.1
```

---

## 配置环境变量

### 可选环境变量

在 `backend/.env` 文件中可以配置：

```env
# Futu OpenD 连接配置（可选）
FUTU_HOST=127.0.0.1      # OpenD 主机地址（默认）
FUTU_PORT=11111          # OpenD 端口（默认）
FUTU_MARKET=US           # 默认市场：US, HK, CN
```

**默认值**：
- `FUTU_HOST=127.0.0.1` - 本地 OpenD 客户端
- `FUTU_PORT=11111` - OpenD 默认端口
- `FUTU_MARKET=US` - 默认市场

---

## 使用方法

### 1. 启动 OpenD 客户端

在启动应用程序之前，确保：

1. ✅ OpenD 客户端已安装
2. ✅ OpenD 客户端正在运行
3. ✅ 已在 OpenD 中登录富途账户
4. ✅ OpenD 显示"已连接"状态

### 2. 启动应用程序

正常启动后端服务：

```bash
cd backend
uvicorn main:app --reload
```

### 3. 配置数据源

在应用的"数据源管理"页面：

1. 导航到 **"数据源"** 页面
2. 找到 **"富途牛牛 (Futu)"** 数据源
3. 点击 **"启用"** 按钮

---

## 功能特性

### 支持的功能

- ✅ 历史K线数据获取
- ✅ 实时行情获取
- ✅ 资金流向数据（港股/A股）
- ✅ 支持港股、美股、A股

### 数据格式

所有数据会自动转换为标准格式：

**历史数据** (`get_stock_data`):
- 列：`Date`, `Open`, `High`, `Low`, `Close`, `Volume`
- 索引：`Date` (DatetimeIndex)

**实时行情** (`get_realtime_quote`):
```json
{
  "price": 150.0,
  "change": 2.5,
  "change_percent": 1.67,
  "volume": 1000000,
  "high": 151.0,
  "low": 149.0,
  "open": 150.5,
  "previous_close": 147.5
}
```

**资金流向** (`get_capital_flow`):
```json
{
  "in_flow": 1000000,
  "out_flow": 800000,
  "net_flow": 200000,
  "large_in": 500000,
  "large_out": 400000,
  "medium_in": 300000,
  "medium_out": 200000,
  "small_in": 200000,
  "small_out": 200000
}
```

---

## 故障排除

### 问题 1: "Futu library not available"

**原因**：`futu` Python 包未安装

**解决**：
```bash
pip install futu==0.0.1
```

### 问题 2: "Failed to connect to Futu OpenD"

**原因**：OpenD 客户端未运行或无法连接

**检查**：
1. ✅ OpenD 客户端是否正在运行？
2. ✅ OpenD 是否显示"已连接"状态？
3. ✅ 端口是否正确（默认 11111）？
4. ✅ 防火墙是否阻止了连接？

**解决**：
- 启动 OpenD 客户端
- 检查 `FUTU_HOST` 和 `FUTU_PORT` 环境变量
- 确认 OpenD 监听地址和端口

### 问题 3: "No data returned from Futu"

**原因**：可能的数据问题

**检查**：
1. ✅ 股票代码格式是否正确？
   - 美股：`AAPL`
   - 港股：`00700.HK`
   - A股：`000001.SZ` 或 `600000.SH`
2. ✅ 日期范围是否有效？
3. ✅ 市场是否匹配？

### 问题 4: Docker 部署中无法使用

**原因**：OpenD 客户端必须在本地运行，Docker 容器无法连接到本地 OpenD

**解决**：
- Futu 功能需要在本地环境使用
- 云端部署（如 Render）无法使用 Futu 功能
- 考虑使用其他数据源（yfinance、Alpha Vantage 等）

---

## 工作原理

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  用户浏览器  │─────▶│  我们的应用   │─────▶│  OpenD客户端 │
│  (前端)     │      │  (后端API)    │      │  (本地运行)  │
└─────────────┘      └──────────────┘      └─────────────┘
                                              │
                                              ▼
                                     ┌─────────────┐
                                     │  富途服务器   │
                                     │  (已登录)     │
                                     └─────────────┘
```

**流程说明**：
1. 用户在我们的应用中请求数据
2. 应用通过 `FutuService` 连接本地 OpenD 客户端
3. OpenD 客户端将请求转发到富途服务器
4. 富途服务器返回数据给 OpenD
5. OpenD 将数据返回给我们的应用
6. 应用处理并返回给用户

---

## 注意事项

### ⚠️ 安全提示

1. **不要将富途账户密码保存在代码中**
   - 登录在 OpenD 客户端完成
   - 应用不需要知道账户密码

2. **本地运行要求**
   - OpenD 客户端必须在本地运行
   - 云端部署无法使用 Futu 功能

3. **网络要求**
   - 需要能够访问富途服务器
   - OpenD 客户端需要稳定的网络连接

### 📝 限制说明

1. **必须本地运行**
   - OpenD 客户端必须在本地安装和运行
   - Docker 容器无法访问本地 OpenD（除非特殊配置）

2. **单用户使用**
   - 一个 OpenD 实例通常对应一个富途账户
   - 多个用户需要多个 OpenD 实例

3. **数据权限**
   - 数据权限取决于富途账户的权限级别
   - 某些高级数据可能需要付费账户

---

## 常见问题

### Q: 我可以在云端部署中使用 Futu 吗？

**A**: 不可以。Futu 功能需要在本地环境使用，因为需要连接到本地运行的 OpenD 客户端。云端部署（如 Render、Heroku 等）无法访问本地 OpenD。

### Q: 如何验证 Futu 是否正常工作？

**A**: 
1. 确保 OpenD 客户端正在运行
2. 在应用的"数据源管理"页面检查 Futu 状态
3. 尝试获取一只股票的数据（如 `AAPL`）

### Q: 是否需要富途账户？

**A**: 是的。需要在 OpenD 客户端中登录富途账户。登录在 OpenD 客户端完成，不需要在我们的应用中输入账户信息。

### Q: 支持哪些市场？

**A**: 支持美股（US）、港股（HK）和A股（CN）。

---

## 参考资源

- **Futu OpenAPI 文档**：https://openapi.futunn.com/
- **OpenD 下载**：https://openapi.futunn.com/download
- **Python SDK 文档**：https://openapi.futunn.com/futu-api-doc/en/

---

## 总结

✅ **Futu 功能已启用** - `futu==0.0.1` 已在 `requirements.txt` 中  
✅ **需要本地 OpenD** - 确保 OpenD 客户端正在运行  
✅ **登录在 OpenD 完成** - 应用不需要账户密码  
✅ **支持多市场** - 美股、港股、A股  

如果遇到问题，请参考故障排除部分或查看 Futu OpenAPI 官方文档。
