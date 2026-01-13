from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, TypeDecorator
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
