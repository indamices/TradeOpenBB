# Fix typing issues for Python 3.11.0a1
try:
    import fix_typing_notrequired
except ImportError:
    try:
        from . import fix_typing_notrequired
    except ImportError:
        pass

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional
import logging

try:
    from .database import get_db, init_db
    from .models import Portfolio, Position, Order, Strategy, AIModelConfig, OrderSide, OrderType, OrderStatus, Base
    from .schemas import (
        Portfolio as PortfolioSchema, PortfolioCreate, PortfolioUpdate,
        Position as PositionSchema, PositionCreate, PositionUpdate,
        Order as OrderSchema, OrderCreate, OrderUpdate,
        Strategy as StrategySchema, StrategyCreate, StrategyUpdate,
        MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse,
        AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse,
        BacktestRequest, BacktestResult
    )
    from .market_service import get_realtime_quote
    from .ai_service_factory import generate_strategy
    from .backtest_engine import run_backtest
except ImportError:
    # Fallback for direct execution
    from database import get_db, init_db
    from models import Portfolio, Position, Order, Strategy, AIModelConfig, OrderSide, OrderType, OrderStatus, Base
    from schemas import (
        Portfolio as PortfolioSchema, PortfolioCreate, PortfolioUpdate,
        Position as PositionSchema, PositionCreate, PositionUpdate,
        Order as OrderSchema, OrderCreate, OrderUpdate,
        Strategy as StrategySchema, StrategyCreate, StrategyUpdate,
        MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse,
        AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse,
        BacktestRequest, BacktestResult
    )
    from market_service import get_realtime_quote
    from ai_service_factory import generate_strategy
    from backtest_engine import run_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartQuant API", version="1.0.0")

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Database integrity error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity error. The operation conflicts with existing data."}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy errors"""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# CORS middleware
# Allow local development and cloud platform domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        # Render platform
        "https://*.render.com",
        # Railway platform
        "https://*.railway.app",
        # Fly.io platform
        "https://*.fly.dev",
        # Vercel platform
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Ensure data directory exists for SQLite
        import os
        data_dir = os.path.join(os.getcwd(), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        # Don't raise - allow app to start even if DB init fails

# Health check
@app.get("/")
async def root():
    return {"message": "SmartQuant API", "status": "running"}

# Portfolio endpoints
@app.get("/api/portfolio", response_model=PortfolioSchema)
async def get_portfolio(portfolio_id: int = 1, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@app.post("/api/portfolio", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
async def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    db_portfolio = Portfolio(
        name=portfolio.name,
        initial_cash=portfolio.initial_cash,
        current_cash=portfolio.initial_cash,
        total_value=portfolio.initial_cash
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@app.put("/api/portfolio/{portfolio_id}", response_model=PortfolioSchema)
async def update_portfolio(portfolio_id: int, portfolio: PortfolioUpdate, db: Session = Depends(get_db)):
    db_portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    update_data = portfolio.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_portfolio, field, value)
    
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

# Position endpoints
@app.get("/api/positions", response_model=List[PositionSchema])
async def get_positions(portfolio_id: int = 1, db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    return positions

@app.post("/api/positions", response_model=PositionSchema, status_code=status.HTTP_201_CREATED)
async def create_position(position: PositionCreate, db: Session = Depends(get_db)):
    position_dict = position.dict()
    # Calculate market_value if not provided
    if 'market_value' not in position_dict:
        position_dict['market_value'] = position_dict['quantity'] * position_dict['current_price']
    db_position = Position(**position_dict)
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    return db_position

# Order endpoints
@app.get("/api/orders", response_model=List[OrderSchema])
async def get_orders(
    portfolio_id: int = 1,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get orders with pagination"""
    orders = db.query(Order)\
        .filter(Order.portfolio_id == portfolio_id)\
        .order_by(Order.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return orders

@app.post("/api/orders", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Verify portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == order.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db_order = Order(**order.dict(), status=OrderStatus.PENDING)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# Strategy endpoints
@app.get("/api/strategies", response_model=List[StrategySchema])
async def get_strategies(portfolio_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Strategy)
    if portfolio_id:
        query = query.filter(Strategy.target_portfolio_id == portfolio_id)
    strategies = query.all()
    return strategies

@app.post("/api/strategies", response_model=StrategySchema, status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    db_strategy = Strategy(**strategy.dict())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

@app.post("/api/strategies/generate", response_model=StrategyGenerationResponse)
async def generate_strategy_endpoint(request: StrategyGenerationRequest, db: Session = Depends(get_db)):
    """Generate strategy code using AI"""
    try:
        result = await generate_strategy(request.prompt, request.model_id, db)
        return result
    except Exception as e:
        logger.error(f"Strategy generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategy generation failed: {str(e)}")

# Market endpoints
@app.get("/api/market/quote/{symbol}", response_model=MarketQuote)
async def get_quote(symbol: str):
    """Get real-time market quote"""
    try:
        quote = await get_realtime_quote(symbol.upper())
        return quote
    except Exception as e:
        logger.error(f"Failed to get quote for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quote: {str(e)}")

# Backtest endpoints
@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest_endpoint(request: BacktestRequest, db: Session = Depends(get_db)):
    """Run backtest for a strategy"""
    try:
        result = await run_backtest(request, db)
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

# AI Model Config endpoints
@app.get("/api/ai-models", response_model=List[AIModelConfigResponse])
async def get_ai_models(db: Session = Depends(get_db)):
    """Get all AI model configurations"""
    models = db.query(AIModelConfig).filter(AIModelConfig.is_active == True).all()
    return models

@app.post("/api/ai-models", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_model(model: AIModelConfigCreate, db: Session = Depends(get_db)):
    """Create new AI model configuration"""
    from ai_service_factory import encrypt_api_key
    
    # Encrypt API key
    encrypted_key = encrypt_api_key(model.api_key)
    
    db_model = AIModelConfig(
        name=model.name,
        provider=model.provider,
        api_key=encrypted_key,
        base_url=model.base_url,
        model_name=model.model_name,
        is_default=False,
        is_active=True
    )
    
    # If this is set as default, unset others
    if model.is_default if hasattr(model, 'is_default') else False:
        db.query(AIModelConfig).update({"is_default": False})
        db_model.is_default = True
    
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@app.put("/api/ai-models/{model_id}", response_model=AIModelConfigResponse)
async def update_ai_model(model_id: int, model: AIModelConfigUpdate, db: Session = Depends(get_db)):
    """Update AI model configuration"""
    from ai_service_factory import encrypt_api_key
    
    db_model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    
    update_data = model.dict(exclude_unset=True)
    
    # Encrypt API key if provided
    if "api_key" in update_data:
        update_data["api_key"] = encrypt_api_key(update_data["api_key"])
    
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model

@app.delete("/api/ai-models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Delete AI model configuration"""
    db_model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    
    db.delete(db_model)
    db.commit()
    return None

@app.post("/api/ai-models/{model_id}/test")
async def test_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Test AI model connection"""
    from ai_service_factory import test_model_connection
    
    try:
        result = await test_model_connection(model_id, db)
        return {"success": True, "message": "Model connection successful"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.put("/api/ai-models/{model_id}/set-default", response_model=AIModelConfigResponse)
async def set_default_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Set default AI model"""
    db_model = db.query(AIModelConfig).filter(AIModelConfig.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="AI model not found")
    
    # Unset all defaults
    db.query(AIModelConfig).update({"is_default": False})
    
    # Set this one as default
    db_model.is_default = True
    db.commit()
    db.refresh(db_model)
    return db_model
