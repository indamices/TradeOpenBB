# 手动测试指南

## 🚀 快速启动

运行启动脚本：
```powershell
.\start_for_testing.ps1
```

或者手动启动：

### 后端
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端
```powershell
npm run dev
```

## 📋 API 端点列表

### 基础端点
- **GET** `/` - 健康检查
- **GET** `/docs` - Swagger API 文档（推荐使用）

### Portfolio（投资组合）

#### 1. 创建投资组合
```http
POST http://localhost:8000/api/portfolio
Content-Type: application/json

{
  "name": "我的测试组合",
  "initial_cash": 100000.0
}
```

**预期响应**: 201 Created
```json
{
  "id": 1,
  "name": "我的测试组合",
  "initial_cash": 100000.0,
  "current_cash": 100000.0,
  "total_value": 100000.0,
  "daily_pnl": 0.0,
  "daily_pnl_percent": 0.0,
  "created_at": "2024-01-13T..."
}
```

#### 2. 获取投资组合
```http
GET http://localhost:8000/api/portfolio?portfolio_id=1
```

**预期响应**: 200 OK

#### 3. 更新投资组合
```http
PUT http://localhost:8000/api/portfolio/1
Content-Type: application/json

{
  "name": "更新后的名称",
  "current_cash": 95000.0
}
```

### Position（持仓）

#### 1. 创建持仓
```http
POST http://localhost:8000/api/positions
Content-Type: application/json

{
  "portfolio_id": 1,
  "symbol": "AAPL",
  "quantity": 10,
  "avg_price": 150.0,
  "current_price": 155.0
}
```

**预期响应**: 201 Created

#### 2. 获取持仓列表
```http
GET http://localhost:8000/api/positions?portfolio_id=1&skip=0&limit=100
```

**参数**:
- `portfolio_id`: 投资组合ID（默认: 1）
- `skip`: 跳过记录数（默认: 0）
- `limit`: 返回记录数（默认: 100）

### Order（订单）

#### 1. 创建订单
```http
POST http://localhost:8000/api/orders
Content-Type: application/json

{
  "portfolio_id": 1,
  "symbol": "AAPL",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 10
}
```

**预期响应**: 201 Created

**注意**: 
- `side`: "BUY" 或 "SELL"
- `type`: "MARKET" 或 "LIMIT"
- 如果 `type` 是 "LIMIT"，需要提供 `limit_price`

#### 2. 获取订单列表
```http
GET http://localhost:8000/api/orders?portfolio_id=1&skip=0&limit=100
```

### Strategy（策略）

#### 1. 获取策略列表
```http
GET http://localhost:8000/api/strategies?skip=0&limit=100
```

#### 2. 创建策略
```http
POST http://localhost:8000/api/strategies
Content-Type: application/json

{
  "name": "简单移动平均策略",
  "logic_code": "def strategy(data):\n    return 'BUY'",
  "description": "一个简单的测试策略",
  "target_portfolio_id": 1,
  "is_active": false
}
```

#### 3. 生成策略（AI）
```http
POST http://localhost:8000/api/strategies/generate
Content-Type: application/json

{
  "prompt": "创建一个简单的移动平均策略",
  "symbol": "AAPL",
  "timeframe": "1d"
}
```

**注意**: 需要先配置 AI 模型（见下方）

### Market（市场数据）

#### 获取实时报价
```http
GET http://localhost:8000/api/market/quote/AAPL
```

**预期响应**: 200 OK 或 500/503（如果市场服务未配置）

### AI Model（AI 模型配置）

#### 1. 获取所有 AI 模型
```http
GET http://localhost:8000/api/ai-models
```

#### 2. 创建 AI 模型配置
```http
POST http://localhost:8000/api/ai-models
Content-Type: application/json

{
  "name": "Gemini Pro",
  "provider": "gemini",
  "api_key": "your_api_key_here",
  "model_name": "gemini-pro",
  "base_url": null
}
```

**provider 选项**: "gemini", "openai", "claude", "custom"

#### 3. 更新 AI 模型
```http
PUT http://localhost:8000/api/ai-models/1
Content-Type: application/json

{
  "name": "Updated Name"
}
```

#### 4. 删除 AI 模型
```http
DELETE http://localhost:8000/api/ai-models/1
```

#### 5. 测试 AI 模型
```http
POST http://localhost:8000/api/ai-models/1/test
```

#### 6. 设置默认模型
```http
PUT http://localhost:8000/api/ai-models/1/set-default
```

### Backtest（回测）

#### 运行回测
```http
POST http://localhost:8000/api/backtest
Content-Type: application/json

{
  "strategy_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_cash": 100000.0,
  "symbols": ["AAPL", "GOOGL"]
}
```

## 🧪 测试场景

### 场景 1: 完整的交易流程

1. **创建投资组合**
   ```bash
   POST /api/portfolio
   {
     "name": "测试组合",
     "initial_cash": 100000.0
   }
   ```
   记录返回的 `portfolio_id`

2. **创建订单**
   ```bash
   POST /api/orders
   {
     "portfolio_id": 1,
     "symbol": "AAPL",
     "side": "BUY",
     "type": "MARKET",
     "quantity": 10
   }
   ```

3. **创建持仓**
   ```bash
   POST /api/positions
   {
     "portfolio_id": 1,
     "symbol": "AAPL",
     "quantity": 10,
     "avg_price": 150.0,
     "current_price": 155.0
   }
   ```

4. **查询投资组合**
   ```bash
   GET /api/portfolio?portfolio_id=1
   ```

5. **查询订单**
   ```bash
   GET /api/orders?portfolio_id=1
   ```

6. **查询持仓**
   ```bash
   GET /api/positions?portfolio_id=1
   ```

### 场景 2: 错误处理测试

1. **获取不存在的投资组合**
   ```bash
   GET /api/portfolio?portfolio_id=99999
   ```
   预期: 404 Not Found

2. **创建无效订单**
   ```bash
   POST /api/orders
   {
     "portfolio_id": 99999,
     "symbol": "",
     "side": "INVALID",
     "type": "MARKET",
     "quantity": -10
   }
   ```
   预期: 422 Validation Error 或 404 Not Found

3. **创建投资组合（零现金）**
   ```bash
   POST /api/portfolio
   {
     "name": "测试",
     "initial_cash": 0.0
   }
   ```
   预期: 422 Validation Error

### 场景 3: 分页测试

1. **创建多个订单**
   - 创建 20 个订单

2. **测试分页**
   ```bash
   GET /api/orders?portfolio_id=1&skip=0&limit=10
   GET /api/orders?portfolio_id=1&skip=10&limit=10
   ```

### 场景 4: 边界条件测试

1. **极大值**
   ```bash
   POST /api/portfolio
   {
     "name": "测试",
     "initial_cash": 1e15
   }
   ```

2. **特殊字符**
   ```bash
   POST /api/portfolio
   {
     "name": "测试组合 🚀 !@#$%",
     "initial_cash": 1000.0
   }
   ```

3. **Unicode 字符**
   ```bash
   POST /api/portfolio
   {
     "name": "测试组合 中文",
     "initial_cash": 1000.0
   }
   ```

## 🛠️ 使用 Swagger UI 测试（推荐）

1. 启动服务后，打开浏览器访问：
   ```
   http://localhost:8000/docs
   ```

2. 在 Swagger UI 中：
   - 查看所有可用的 API 端点
   - 点击端点展开详情
   - 点击 "Try it out" 按钮
   - 填写参数
   - 点击 "Execute" 执行请求
   - 查看响应结果

3. **优势**:
   - 无需手动编写 HTTP 请求
   - 自动生成请求格式
   - 实时查看响应
   - 可以测试所有端点

## 📊 使用 Postman 或 curl 测试

### curl 示例

#### 创建投资组合
```bash
curl -X POST "http://localhost:8000/api/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试组合",
    "initial_cash": 100000.0
  }'
```

#### 获取投资组合
```bash
curl "http://localhost:8000/api/portfolio?portfolio_id=1"
```

#### 创建订单
```bash
curl -X POST "http://localhost:8000/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "symbol": "AAPL",
    "side": "BUY",
    "type": "MARKET",
    "quantity": 10
  }'
```

## ✅ 测试检查清单

- [ ] 健康检查端点正常
- [ ] 可以创建投资组合
- [ ] 可以获取投资组合
- [ ] 可以更新投资组合
- [ ] 可以创建订单
- [ ] 可以创建持仓
- [ ] 分页功能正常
- [ ] 错误处理正常（404, 422）
- [ ] 输入验证正常
- [ ] 特殊字符处理正常
- [ ] Unicode 字符处理正常

## 🐛 常见问题

### 1. 后端无法启动
- 检查 Python 是否安装
- 检查依赖是否安装：`pip install -r backend/requirements.txt`
- 检查端口 8000 是否被占用

### 2. 数据库错误
- 确保 `.env` 文件存在
- 运行数据库初始化：`python -c "from database import init_db; init_db()"`

### 3. 404 错误
- 检查端点路径是否正确
- 检查资源是否存在（如 portfolio_id）

### 4. 422 验证错误
- 检查请求体格式
- 检查必填字段是否提供
- 检查字段类型和值是否符合要求

## 📝 测试记录模板

```
测试日期: ___________
测试人员: ___________

测试项目: ___________
端点: ___________
请求: ___________
预期结果: ___________
实际结果: ___________
状态: [ ] 通过 [ ] 失败
备注: ___________
```

## 🎯 下一步

测试完成后，可以：
1. 查看测试结果
2. 报告发现的 bugs
3. 验证性能
4. 检查错误处理
