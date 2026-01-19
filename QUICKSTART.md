# 代码质量修复快速开始指南

本指南帮助你在 **30 分钟内**开始修复代码质量问题。

## 📋 前置条件

- Node.js 和 npm 已安装
- 项目可以正常运行
- 有 TypeScript 基础知识

## 🚀 快速开始（3 步）

### 第 1 步：更新导入语句（5 分钟）

在你的组件文件中，添加新的安全工具导入：

```typescript
// 在文件顶部添加
import {
  safeToFixed,
  safeCurrency,
  safePercent,
  safeSignedPercent,
  safeSignedCurrency,
  formatMetric,
  formatDate
} from '../utils/format';

import {
  safeArrayAccess,
  safeArrayMap,
  safeNumber
} from '../utils/safeHelpers';
```

### 第 2 步：替换不安全的代码（15 分钟）

#### 示例 1: 修复 `.toFixed()` 调用

**之前**:
```typescript
<td>{pos.avg_price.toFixed(2)}</td>
```

**之后**:
```typescript
<td>{safeCurrency(pos.avg_price)}</td>
```

#### 示例 2: 修复百分比显示

**之前**:
```typescript
<span>{(result.total_return * 100).toFixed(2)}%</span>
```

**之后**:
```typescript
<span>{safePercent(result.total_return)}</span>
```

#### 示例 3: 修复数组访问

**之前**:
```typescript
{indicators[0] && Object.keys(indicators[0]).map(...)}
```

**之后**:
```typescript
{safeArrayAccess(indicators, 0, null) && Object.keys(...).map(...)}
```

#### 示例 4: 修复条件渲染

**之前**:
```typescript
{portfolio.daily_pnl >= 0 ? '+' : ''}{portfolio.daily_pnl_percent.toFixed(2)}%
```

**之后**:
```typescript
{safeSignedPercent(portfolio.daily_pnl_percent)}
```

### 第 3 步：添加错误边界（10 分钟）

在 `App.tsx` 中包裹你的应用：

```typescript
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      {/* 你的路由和组件 */}
      <Routes>
        {/* ... */}
      </Routes>
    </ErrorBoundary>
  );
}
```

## 📝 修复清单

使用此清单逐个文件修复：

### 高优先级文件

- [ ] **Dashboard.tsx**
  - [ ] 第 405-410 行: 持仓表格数值
  - [ ] 第 443-451 行: 市场报价表格

- [ ] **PortfolioManager.tsx**
  - [ ] 第 342-346 行: 持仓列表
  - [ ] 第 172-173 行: 百分比显示

- [ ] **BacktestLab.tsx**
  - [ ] 第 413-444 行: 性能指标卡片
  - [ ] 第 596-622 行: 个股盈亏分析

- [ ] **BacktestRecords.tsx**
  - [ ] 第 144-147 行: formatMetric 函数（改用导入的版本）

- [ ] **AIAnalysis.tsx**
  - [ ] 第 47-50 行: formatMetric 函数（改用导入的版本）

### 中优先级文件

- [ ] **StrategyLab.tsx**
  - [ ] 第 81 行: 消除 `any` 类型

- [ ] **StrategyManager.tsx**
  - [ ] 第 39, 74, 87, 99, 125 行: 统一错误处理

- [ ] **StockPoolManager.tsx**
  - [ ] 第 206-209 行: 过滤逻辑安全化

## 🛠️ 使用自动修复脚本（可选）

如果你想要自动化部分修复：

```bash
# 运行自动修复脚本
node scripts/fix-null-safety.js
```

**注意**: 脚本会创建 `.bak` 备份文件，请检查修改后的内容。

## ✅ 验证修复

修复完成后，运行以下检查：

### 1. TypeScript 编译
```bash
npm run type-check
# 或
npx tsc --noEmit
```

### 2. ESLint 检查
```bash
npm run lint
```

### 3. 运行应用
```bash
npm run dev
```

### 4. 手动测试
- 访问所有主要页面
- 检查数值显示是否正常
- 检查空数据状态
- 测试错误处理

## 📚 常用代码模式

### 显示货币值
```typescript
// ❌ 错误
${price.toFixed(2)}

// ✅ 正确
{safeCurrency(price)}
```

### 显示百分比
```typescript
// ❌ 错误
{(value * 100).toFixed(2)}%

// ✅ 正确
{safePercent(value)}
```

### 显示带符号百分比
```typescript
// ❌ 错误
{value >= 0 ? '+' : ''}{(value * 100).toFixed(2)}%

// ✅ 正确
{safeSignedPercent(value)}
```

### 显示带符号货币
```typescript
// ❌ 错误
{value >= 0 ? '+' : ''}${value.toFixed(2)}

// ✅ 正确
{safeSignedCurrency(value)}
```

### 格式化日期
```typescript
// ❌ 错误
{new Date(dateString).toLocaleDateString()}

// ✅ 正确
{formatDate(dateString, 'zh-CN')}
```

### 数组操作
```typescript
// ❌ 错误
items.map(item => item.value)
items.filter(item => item.active)

// ✅ 正确
safeArrayMap(items, item => item.value)
safeArrayFilter(items, item => item.active)
```

## 🆘 遇到问题？

### 问题 1: 找不到模块

**错误**:
```
Cannot find module '../utils/safeHelpers'
```

**解决**:
```bash
# 确保文件存在
ls utils/safeHelpers.ts
ls utils/format.ts
ls types/extended.ts
```

### 问题 2: 类型错误

**错误**:
```
Type 'number | undefined' is not assignable to type 'number'
```

**解决**:
使用安全工具函数，它们已经处理了 undefined：
```typescript
// ❌ 错误
const value: number = data.value;

// ✅ 正确
const value: number = safeNumber(data.value, 0);
```

### 问题 3: 性能下降

**解决**:
添加 `useMemo` 缓存计算结果：
```typescript
import { useMemo } from 'react';

const formattedData = useMemo(() => {
  return data.map(item => ({
    ...item,
    value: formatMetric(item.value)
  }));
}, [data]);
```

## 📖 更多资源

- **详细修复指南**: 查看 `FIXES_GUIDE.md`
- **完整审查报告**: 查看 `CODE_REVIEW_REPORT.md`
- **工具函数文档**: 查看 `utils/safeHelpers.ts` 和 `utils/format.ts`
- **类型定义**: 查看 `types/extended.ts`
- **React Hooks**: 查看 `hooks/index.ts`

## 🎯 下一步

完成快速修复后，建议：

1. **本周**: 完成所有高优先级修复
2. **下周**: 处理中优先级问题（性能优化）
3. **第三周**: 处理低优先级问题（代码一致性）

## 💡 最佳实践

- 每次修复一个文件
- 修复后立即测试
- 提交前运行 TypeScript 和 ESLint 检查
- 编写单元测试覆盖修复的代码
- 使用 git commits 追踪修复进度

---

**预计完成时间**: 8-12 小时
**优先级**: 高
**影响**: 提高代码质量和用户体验
