# 测试指南

## 测试概述

本项目的测试分为以下几个部分：
1. **参数优化功能测试** - `test_parameter_optimizer.py`
2. **AI策略分析测试** - `test_strategy_analyzer.py`
3. **富途OpenAPI集成测试** - `test_futu_service.py`
4. **回测记录功能测试** - `test_backtest_records.py`

## 运行测试

### 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-mock
```

### 运行所有测试

```bash
# 在backend目录下
cd backend
pytest tests/ -v

# 或者运行测试脚本
python tests/run_tests.py
```

### 运行特定测试文件

```bash
# 测试参数优化
pytest tests/test_parameter_optimizer.py -v

# 测试AI策略分析
pytest tests/test_strategy_analyzer.py -v

# 测试富途服务
pytest tests/test_futu_service.py -v

# 测试回测记录
pytest tests/test_backtest_records.py -v
```

### 运行特定测试类

```bash
# 运行参数提取测试
pytest tests/test_parameter_optimizer.py::TestParameterExtraction -v

# 运行参数替换测试
pytest tests/test_parameter_optimizer.py::TestParameterReplacement -v
```

### 运行特定测试方法

```bash
# 运行单个测试方法
pytest tests/test_parameter_optimizer.py::TestParameterExtraction::test_extract_parameters_simple -v
```

## 测试覆盖率

要生成测试覆盖率报告，需要安装 `pytest-cov`：

```bash
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest tests/ --cov=services --cov=backtest_engine --cov-report=html

# 查看HTML报告
# 打开 htmlcov/index.html
```

## 测试说明

### 1. 参数优化测试 (`test_parameter_optimizer.py`)

测试覆盖：
- ✅ 参数提取功能
- ✅ 参数替换功能
- ✅ 参数组合生成
- ✅ 完整的优化流程
- ✅ 错误处理

**Mock说明**：
- 使用Mock对象模拟数据库会话
- 使用AsyncMock模拟`run_backtest`函数
- 模拟策略和回测结果

### 2. AI策略分析测试 (`test_strategy_analyzer.py`)

测试覆盖：
- ✅ 结构化分析功能
- ✅ 指标评级功能
- ✅ AI响应解析
- ✅ 错误处理

**Mock说明**：
- 模拟AI服务提供者
- 模拟数据库查询
- 测试AI不可用时的回退行为

### 3. 富途服务测试 (`test_futu_service.py`)

测试覆盖：
- ✅ 服务初始化
- ✅ 市场类型检测
- ✅ 数据获取功能
- ✅ 可用性检查
- ✅ 上下文管理器

**注意**：
- 如果未安装`futu`库，某些测试会被跳过
- 使用Mock对象模拟futu库
- 测试不依赖实际的OpenD连接

### 4. 回测记录测试 (`test_backtest_records.py`)

测试覆盖：
- ✅ 记录模型创建
- ✅ Schema验证
- ✅ CSV导出结构
- ✅ Excel导出结构（需要openpyxl）

## 已知问题和限制

1. **富途服务测试**：
   - 需要futu库或完整的Mock实现
   - 某些测试可能在没有futu库时被跳过

2. **Excel导出测试**：
   - 需要openpyxl库
   - 如果没有安装，相关测试会被跳过

3. **参数优化测试**：
   - 使用Mock的`run_backtest`，不会实际执行回测
   - 需要确保Mock返回的数据结构正确

4. **数据库依赖**：
   - 所有测试都使用Mock数据库会话
   - 不需要实际的数据库连接

## 持续集成

要在CI/CD环境中运行测试：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov
    pytest tests/ --cov=services --cov-report=xml
```

## 调试测试

如果测试失败，可以使用以下选项：

```bash
# 显示详细输出
pytest tests/ -v -s

# 显示打印语句
pytest tests/ -s

# 在第一个失败时停止
pytest tests/ -x

# 显示详细回溯
pytest tests/ --tb=long

# 运行上次失败的测试
pytest tests/ --lf
```

## 编写新测试

添加新测试时，请遵循以下原则：

1. **测试命名**：使用描述性的测试名称
2. **测试独立性**：每个测试应该独立运行
3. **Mock外部依赖**：使用Mock对象模拟外部服务
4. **清理资源**：在测试后清理创建的资源
5. **使用fixture**：重用常用的测试数据

示例：

```python
@pytest.fixture
def sample_data():
    """提供测试数据"""
    return {"key": "value"}

def test_something(sample_data):
    """测试某个功能"""
    assert sample_data["key"] == "value"
```

## 测试最佳实践

1. **快速反馈**：测试应该快速运行
2. **可重复性**：测试结果应该一致
3. **隔离性**：测试不应该相互依赖
4. **清晰性**：测试代码应该易于理解
5. **覆盖关键路径**：优先测试关键业务逻辑
