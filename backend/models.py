from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, TypeDecorator, Date, BigInteger, Index, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class OrderSide(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"

class AIProvider(enum.Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    CUSTOM = "custom"

class AIProviderType(TypeDecorator):
    """Custom type for AIProvider enum that handles string values correctly"""
    impl = String(50)
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=50)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to string when saving to database"""
        if value is None:
            return None
        if isinstance(value, AIProvider):
            return value.value
        # If it's already a string, validate it
        if isinstance(value, str):
            try:
                # Validate by trying to create enum
                AIProvider(value.lower())
                return value.lower()
            except (ValueError, AttributeError):
                return value.lower()  # Use as-is for backward compatibility
        return str(value).lower()
    
    def process_result_value(self, value, dialect):
        """Convert string to enum when reading from database"""
        if value is None:
            return None
        if isinstance(value, AIProvider):
            return value
        # Try to convert string to enum
        if isinstance(value, str):
            try:
                return AIProvider(value.lower())
            except (ValueError, AttributeError):
                # If conversion fails, return the string (will be handled in API layer)
                return value
        return value

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    initial_cash = Column(Float, nullable=False)
    current_cash = Column(Float, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)
    daily_pnl = Column(Float, default=0)
    daily_pnl_percent = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="portfolio", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0)
    unrealized_pnl_percent = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    portfolio = relationship("Portfolio", back_populates="positions")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(Integer, nullable=False)
    limit_price = Column(Float, nullable=True)
    avg_fill_price = Column(Float, nullable=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    commission = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    
    portfolio = relationship("Portfolio", back_populates="orders")

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    logic_code = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    target_portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    portfolio = relationship("Portfolio", back_populates="strategies")

class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # Use custom TypeDecorator to handle enum conversion properly
    provider = Column(AIProviderType(), nullable=False)
    api_key = Column(Text, nullable=False)  # Will be encrypted
    base_url = Column(String(500), nullable=True)  # For custom/local models
    model_name = Column(String(255), nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketData(Base):
    """Historical OHLCV market data"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Composite unique index and index for efficient queries
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uq_symbol_date'),
        Index('idx_symbol_date', 'symbol', 'date'),
    )


class StockPool(Base):
    """Stock pool management for backtesting"""
    __tablename__ = "stock_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    symbols = Column(JSON, nullable=False)  # List[str]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockInfo(Base):
    """Stock basic information cache"""
    __tablename__ = "stock_info"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(50), nullable=True)
    market_type = Column(String(20), nullable=True, index=True)  # 'US', 'HK', 'CN' (A股)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataSyncLog(Base):
    """Data synchronization log for tracking sync operations"""
    __tablename__ = "data_sync_log"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    sync_type = Column(String(50), nullable=True)  # 'historical', 'realtime', 'info'
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    records_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=True)  # 'success', 'failed', 'partial'
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    """Chat conversation session"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=True)  # 会话标题（从第一条消息提取）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    strategies = relationship("ChatStrategy", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """Individual message in a conversation"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    code_snippets = Column(JSON, nullable=True)  # {"python": "code..."}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")


class ChatStrategy(Base):
    """Strategy extracted from chat conversation"""
    __tablename__ = "chat_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id"), nullable=True, index=True)
    message_id = Column(Integer, ForeignKey("conversation_messages.id"), nullable=True)  # 来源消息
    name = Column(String(255), nullable=False)  # 策略名称（自动提取或用户输入）
    logic_code = Column(Text, nullable=False)  # 策略代码
    description = Column(Text, nullable=True)  # 策略描述
    is_saved = Column(Boolean, default=False)  # 是否已保存到策略池
    saved_strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)  # 关联的策略池ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="strategies")
    saved_strategy = relationship("Strategy", foreign_keys=[saved_strategy_id])


class BacktestSymbolList(Base):
    """Saved symbol lists for backtesting"""
    __tablename__ = "backtest_symbol_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 清单名称
    description = Column(Text, nullable=True)  # 描述
    symbols = Column(JSON, nullable=False)  # List[str]
    is_active = Column(Boolean, default=True)  # 是否活跃
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataSourceConfig(Base):
    """Data source configuration for market data"""
    __tablename__ = "data_source_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)  # e.g., 'OpenBB', 'Yahoo Finance', 'Alpha Vantage'
    source_type = Column(String(50), nullable=False)  # 'free', 'paid', 'api', 'direct'
    provider = Column(String(100), nullable=False)  # 'openbb', 'yfinance', 'alphavantage', 'polygon', etc.
    api_key = Column(Text, nullable=True)  # Encrypted API key if needed
    base_url = Column(String(500), nullable=True)  # Base URL for API
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Higher priority = used first
    supports_markets = Column(JSON, nullable=True)  # ['US', 'HK', 'CN'] - which markets are supported
    rate_limit = Column(Integer, nullable=True)  # Requests per minute
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BacktestRecord(Base):
    """回测记录表"""
    __tablename__ = "backtest_records"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)  # 回测名称（用户可自定义）
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    strategy_name = Column(String(255), nullable=True)  # 策略名称快照
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_cash = Column(Float, nullable=False)
    symbols = Column(JSON, nullable=False)  # List[str] - 回测的股票列表
    
    # 回测结果指标
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    total_return = Column(Float, nullable=True)
    
    # 详细结果（JSON存储完整结果）
    full_result = Column(JSON, nullable=True)  # 完整的BacktestResult JSON
    
    # 回测参数
    compare_with_indices = Column(Boolean, default=False)
    compare_items = Column(JSON, nullable=True)  # List[str]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    strategy = relationship("Strategy", foreign_keys=[strategy_id])
    
    __table_args__ = (
        Index('idx_backtest_strategy_date', 'strategy_id', 'created_at'),
        Index('idx_backtest_created', 'created_at'),
    )
