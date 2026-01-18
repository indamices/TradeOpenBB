from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    CUSTOM = "custom"

# Portfolio Schemas
class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    initial_cash: float = Field(..., gt=0, le=1e15)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    current_cash: Optional[float] = None
    total_value: Optional[float] = None
    daily_pnl: Optional[float] = None
    daily_pnl_percent: Optional[float] = None

class Portfolio(PortfolioBase):
    id: int
    current_cash: float
    total_value: float
    daily_pnl: float
    daily_pnl_percent: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Position Schemas
class PositionBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: int = Field(..., gt=0, le=999999999)
    avg_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()

class PositionCreate(PositionBase):
    portfolio_id: int

class PositionUpdate(BaseModel):
    quantity: Optional[int] = None
    avg_price: Optional[float] = None
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None

class Position(PositionBase):
    id: int
    portfolio_id: int
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    type: OrderType
    quantity: int = Field(..., gt=0, le=999999999)
    limit_price: Optional[float] = Field(None, gt=0)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or not v.strip():
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()

class OrderCreate(OrderBase):
    portfolio_id: int

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    avg_fill_price: Optional[float] = None
    filled_at: Optional[datetime] = None

class Order(OrderBase):
    id: int
    portfolio_id: int
    status: OrderStatus
    avg_fill_price: Optional[float]
    commission: float
    created_at: datetime
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Strategy Schemas
class StrategyBase(BaseModel):
    name: str
    logic_code: str
    description: Optional[str] = None

class StrategyCreate(StrategyBase):
    target_portfolio_id: int
    is_active: bool = False

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    logic_code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Strategy(StrategyBase):
    id: int
    is_active: bool
    target_portfolio_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Market Quote Schema
class MarketQuote(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    last_updated: datetime

# AI Model Config Schemas
class AIModelConfigBase(BaseModel):
    name: str
    provider: AIProvider
    model_name: str
    base_url: Optional[str] = None

class AIModelConfigCreate(AIModelConfigBase):
    api_key: str

class AIModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class AIModelConfigResponse(AIModelConfigBase):
    id: int
    is_default: bool
    is_active: bool
    created_at: datetime
    # Note: api_key is not included in response for security
    
    class Config:
        from_attributes = True

# Strategy Generation Schemas
class StrategyGenerationRequest(BaseModel):
    prompt: str
    model_id: Optional[int] = None  # If None, use default model

class StrategyGenerationResponse(BaseModel):
    code: str
    explanation: str

# AI Chat Schemas
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    suggestions: Optional[List[str]] = None
    code_snippets: Optional[Dict[str, str]] = None

# Stock Pool Schemas
class StockPoolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    symbols: List[str] = Field(..., min_items=1)
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('Symbols list cannot be empty')
        # Normalize symbols to uppercase
        return [s.upper().strip() for s in v if s.strip()]

class StockPoolCreate(StockPoolBase):
    pass

class StockPoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    symbols: Optional[List[str]] = None
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if v is not None:
            if not v:
                raise ValueError('Symbols list cannot be empty')
            return [s.upper().strip() for s in v if s.strip()]
        return v

class StockPool(StockPoolBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Stock Info Schemas
class StockInfo(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    market_type: Optional[str] = None  # 'US', 'HK', 'CN' (A股)
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Data Sync Schemas
class DataSyncRequest(BaseModel):
    symbols: List[str] = Field(..., min_items=1)
    start_date: str  # ISO format date
    end_date: str  # ISO format date
    sync_type: str = "historical"  # 'historical', 'realtime', 'info'

class DataSyncResponse(BaseModel):
    success: bool
    message: str
    symbols_processed: int
    records_added: int

# Conversation Schemas
class ConversationBase(BaseModel):
    title: Optional[str] = None

class Conversation(ConversationBase):
    id: int
    conversation_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0  # 消息数量
    
    class Config:
        from_attributes = True

class ConversationMessage(BaseModel):
    id: int
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    code_snippets: Optional[Dict[str, str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ChatStrategy Schemas
class ChatStrategyBase(BaseModel):
    name: str
    logic_code: str
    description: Optional[str] = None

class ChatStrategyCreate(ChatStrategyBase):
    conversation_id: str
    message_id: Optional[int] = None

class ChatStrategy(ChatStrategyBase):
    id: int
    conversation_id: str
    message_id: Optional[int] = None
    is_saved: bool
    saved_strategy_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SaveStrategyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_portfolio_id: int = 1

# BacktestSymbolList Schemas
class SymbolListBase(BaseModel):
    name: str
    description: Optional[str] = None
    symbols: List[str]

class SymbolListCreate(SymbolListBase):
    pass

class SymbolListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    symbols: Optional[List[str]] = None

# Data Source Config Schemas
class DataSourceConfigBase(BaseModel):
    name: str
    source_type: str  # 'free', 'paid', 'api', 'direct'
    provider: str  # 'openbb', 'yfinance', 'alphavantage', 'polygon', etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    priority: int = 0
    supports_markets: Optional[List[str]] = None  # ['US', 'HK', 'CN']
    rate_limit: Optional[int] = None

class DataSourceConfigCreate(DataSourceConfigBase):
    pass

class DataSourceConfigUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None
    supports_markets: Optional[List[str]] = None
    rate_limit: Optional[int] = None

class DataSourceConfigResponse(DataSourceConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    is_active: Optional[bool] = None

class SymbolList(SymbolListBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Strategy Active Status Schemas
class SetStrategyActiveRequest(BaseModel):
    is_active: bool

class BatchSetActiveRequest(BaseModel):
    strategy_ids: List[int]
    is_active: bool

# Backtest Schemas
class BacktestRequest(BaseModel):
    strategy_id: int
    start_date: str  # ISO format date
    end_date: str
    initial_cash: float = Field(gt=0)
    symbols: List[str] = Field(min_items=1)
    compare_with_indices: bool = False  # Whether to compare with market indices
    compare_items: Optional[List[str]] = None  # List of items to compare: ['NASDAQ', 'SMA_CROSS', 'MOMENTUM', etc.]

class BacktestResult(BaseModel):
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    annualized_return: float
    max_drawdown: float
    win_rate: Optional[float] = None
    total_trades: int
    total_return: float
    # Time series data
    equity_curve: Optional[List[Dict[str, Any]]] = None  # [{date: str, value: float}, ...]
    drawdown_series: Optional[List[Dict[str, Any]]] = None  # [{date: str, drawdown: float}, ...]
    trades: Optional[List[Dict[str, Any]]] = None  # [{date, symbol, side, price, quantity, commission, trigger_reason, pnl, pnl_percent}, ...]
    per_stock_performance: Optional[List[Dict[str, Any]]] = None  # Per-stock performance breakdown
    index_comparisons: Optional[List[Dict[str, Any]]] = None  # Comparison with market indices
    strategy_comparisons: Optional[Dict[str, Any]] = None  # Strategy comparison results


# Backtest Record Schemas
class BacktestRecordBase(BaseModel):
    name: Optional[str] = None
    strategy_id: int
    start_date: date
    end_date: date
    initial_cash: float
    symbols: List[str]
    compare_with_indices: Optional[bool] = False
    compare_items: Optional[List[str]] = None

class BacktestRecordCreate(BacktestRecordBase):
    pass

class BacktestRecordUpdate(BaseModel):
    name: Optional[str] = None

class BacktestRecord(BacktestRecordBase):
    id: int
    strategy_name: Optional[str] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    annualized_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    total_return: Optional[float] = None
    full_result: Optional[Dict[str, Any]] = None
    compare_with_indices: Optional[bool] = False
    compare_items: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Parameter Optimization Schemas
class ParameterOptimizationRequest(BaseModel):
    strategy_id: int
    start_date: str  # ISO format date
    end_date: str
    initial_cash: float = Field(gt=0, default=100000)
    symbols: List[str] = Field(min_items=1)
    parameter_ranges: Dict[str, List[Any]] = Field(default_factory=dict)  # e.g., {"short_sma": [10, 20, 30], "long_sma": [50, 100, 200]}
    optimization_metric: str = Field(default="sharpe_ratio")  # sharpe_ratio, sortino_ratio, annualized_return, total_return, win_rate, max_drawdown

class ParameterOptimizationResult(BaseModel):
    best_parameters: Dict[str, Any]
    best_metric_value: float
    optimization_metric: str
    results: List[Dict[str, Any]]  # List of {parameters: {...}, metrics: BacktestResult, ...}
    total_combinations: int
    # Optional fields for backward compatibility
    best_result: Optional[Dict[str, Any]] = None  # Best BacktestResult (deprecated, use results[0])
    all_results: Optional[List[Dict[str, Any]]] = None  # Deprecated, use results
    valid_combinations: Optional[int] = None

# AI Strategy Analysis Schemas
class AIStrategyAnalysisRequest(BaseModel):
    backtest_result: BacktestResult
    strategy_id: int

class AIStrategyAnalysisResponse(BaseModel):
    analysis_summary: str
    strengths: List[str]
    weaknesses: List[str]
    optimization_suggestions: List[str]
    raw_ai_response: Optional[str] = None