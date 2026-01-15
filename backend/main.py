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
from typing import List, Optional, Dict
import logging
import time

# Use absolute imports for Docker deployment
from database import get_db, init_db
from models import Portfolio, Position, Order, Strategy, AIModelConfig, OrderSide, OrderType, OrderStatus, AIProvider, Base, StockPool, StockInfo
from schemas import (
    Portfolio as PortfolioSchema, PortfolioCreate, PortfolioUpdate,
    Position as PositionSchema, PositionCreate, PositionUpdate,
    Order as OrderSchema, OrderCreate, OrderUpdate,
    Strategy as StrategySchema, StrategyCreate, StrategyUpdate,
    MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse,
    AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse,
    BacktestRequest, BacktestResult, ChatRequest, ChatResponse,
    StockPool as StockPoolSchema, StockPoolCreate, StockPoolUpdate,
    StockInfo as StockInfoSchema, DataSyncRequest, DataSyncResponse
)
from market_service import get_realtime_quote, get_multiple_quotes, get_market_overview, get_technical_indicators
from ai_service_factory import generate_strategy, chat_with_ai
from backtest_engine import run_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory conversation storage (in production, use database)
conversation_storage: Dict[str, List[Dict]] = {}

app = FastAPI(title="SmartQuant API", version="1.0.0")

# Add rate limiting middleware (60 requests per minute per IP)
try:
    from middleware import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    logger.info("Rate limiting middleware enabled")
except Exception as e:
    logger.warning(f"Failed to enable rate limiting middleware: {str(e)}")

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
    error_str = str(exc)
    logger.error(f"Database error: {error_str}", exc_info=True)
    
    # Provide more user-friendly error messages for common database errors
    if "could not translate host name" in error_str.lower() or "name or service not known" in error_str.lower():
        detail = (
            "Database connection error: Unable to resolve database hostname. "
            "Please check your DATABASE_URL configuration in Render Dashboard. "
            "Use the External Connection String (with full domain name) instead of Internal. "
            "See RENDER_POSTGRESQL_SETUP.md for detailed instructions."
        )
    elif "connection refused" in error_str.lower() or "connection timeout" in error_str.lower():
        detail = (
            "Database connection error: Unable to connect to database server. "
            "Please check if the database service is running and accessible."
        )
    elif "authentication failed" in error_str.lower() or "password authentication failed" in error_str.lower():
        detail = (
            "Database authentication error: Invalid username or password. "
            "Please check your DATABASE_URL configuration in Render Dashboard."
        )
    elif "database" in error_str.lower() and "does not exist" in error_str.lower():
        detail = (
            "Database error: The specified database does not exist. "
            "Please check your DATABASE_URL configuration."
        )
    else:
        detail = f"Database error occurred: {error_str}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # #region agent log
    try:
        import os, json
        log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main.py:113","message":"Exception handler triggered","data":{"path":request.url.path,"method":request.method,"exception_type":type(exc).__name__,"exception_msg":str(exc)[:100],"origin":request.headers.get("origin")}})+'\n')
    except Exception as log_exc:
        # Don't fail if logging fails - just log to stderr
        logger.error(f"Failed to write debug log: {log_exc}")
    # #endregion
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
    # Ensure CORS headers are added even for errors
    origin = request.headers.get("origin")
    if origin:
        # Check if origin is allowed
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://tradeopenbb-frontend.onrender.com",
        ]
        import re
        origin_pattern = re.compile(r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app")
        
        if origin in allowed_origins or origin_pattern.match(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            # #region agent log
            try:
                import os, json
                log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main.py:148","message":"CORS headers added to exception response","data":{"origin":origin}})+'\n')
            except Exception as log_exc:
                logger.error(f"Failed to write debug log: {log_exc}")
            # #endregion
    return response

# CORS middleware - MUST be added BEFORE RateLimitMiddleware
# In FastAPI, middleware executes in reverse order (last added = first executed)
# So we add CORS last so it wraps all responses, but it will execute first
# Allow local development and cloud platform domains
# Use allow_origin_regex for pattern matching to support wildcard domains
import re

# Add a simple middleware to log CORS processing
@app.middleware("http")
async def cors_ensuring_middleware(request: Request, call_next):
    # #region agent log
    try:
        import os, json
        log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:157","message":"CORS ensuring middleware entry","data":{"path":request.url.path,"method":request.method,"origin":request.headers.get("origin")}})+'\n')
    except: pass
    # #endregion
    
    # Handle OPTIONS preflight explicitly
    if request.method == "OPTIONS":
        # #region agent log
        try:
            import os, json
            log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"main.py:178","message":"Handling OPTIONS preflight","data":{"path":request.url.path,"origin":request.headers.get("origin")}})+'\n')
        except: pass
        # #endregion
        origin = request.headers.get("origin")
        response = JSONResponse(content={}, status_code=200)
        if origin:
            allowed_origins = ["http://localhost:3000", "http://localhost:5173", "https://tradeopenbb-frontend.onrender.com"]
            import re
            origin_pattern = re.compile(r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app")
            if origin in allowed_origins or origin_pattern.match(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Max-Age"] = "3600"
                # #region agent log
                try:
                    import os, json
                    log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"main.py:203","message":"OPTIONS response with CORS headers","data":{"origin":origin}})+'\n')
                except: pass
                # #endregion
        return response
    
    response = await call_next(request)
    
    # Ensure CORS headers are present on all responses
    origin = request.headers.get("origin")
    if origin and "Access-Control-Allow-Origin" not in response.headers:
        allowed_origins = ["http://localhost:3000", "http://localhost:5173", "https://tradeopenbb-frontend.onrender.com"]
        import re
        origin_pattern = re.compile(r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app")
        if origin in allowed_origins or origin_pattern.match(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            # #region agent log
            try:
                import os, json
                log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:227","message":"Added CORS headers to response","data":{"origin":origin,"path":request.url.path}})+'\n')
            except: pass
            # #endregion
    
    # #region agent log
    try:
        import os, json
        log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        cors_headers = {k:v for k,v in response.headers.items() if 'access-control' in k.lower()}
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:236","message":"CORS ensuring middleware exit","data":{"path":request.url.path,"status_code":response.status_code,"cors_headers":cors_headers}})+'\n')
    except: pass
    # #endregion
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "https://tradeopenbb-frontend.onrender.com",  # Render frontend
    ],
    allow_origin_regex=r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicitly list methods
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Start task scheduler for background data sync
    try:
        from services.scheduler import scheduler
        scheduler.start()
        logger.info("Task scheduler started successfully")
    except Exception as e:
        logger.warning(f"Failed to start task scheduler: {e}. Scheduled tasks will be disabled.")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    try:
        from services.scheduler import scheduler
        scheduler.stop()
        logger.info("Task scheduler stopped")
    except Exception:
        pass
    try:
        # Ensure data directory exists for SQLite
        import os
        data_dir = os.path.join(os.getcwd(), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        init_db()
        logger.info("Database initialized successfully")
        
        # Verify default portfolio exists
        db = next(get_db())
        try:
            portfolio = db.query(Portfolio).filter(Portfolio.id == 1).first()
            if portfolio:
                logger.info(f"Verified default portfolio exists: {portfolio.name} (ID: {portfolio.id})")
            else:
                logger.warning("Default portfolio (ID=1) not found after initialization")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        # Don't raise - allow app to start even if DB init fails

# Health check
@app.get("/")
@app.get("/health")
async def root():
    """Health check endpoint - optimized for fast response"""
    return {"message": "SmartQuant API", "status": "running", "timestamp": time.time()}

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
    # Verify portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == position.portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
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

# AI Chat endpoints
@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """AI chat conversation"""
    # #region agent log
    try:
        import os, json
        log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"main.py:354","message":"chat_endpoint called","data":{"path":"/api/ai/chat","message_length":len(request.message)}})+'\n')
    except: pass
    # #endregion
    try:
        import uuid
        from datetime import datetime
        
        # Get or create conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if new
        if conversation_id not in conversation_storage:
            conversation_storage[conversation_id] = []
        
        # Add user message to history
        conversation_storage[conversation_id].append({
            'role': 'user',
            'content': request.message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Use dedicated chat function instead of strategy generation
        # This allows for natural conversation without requiring JSON format
        conversation_history = conversation_storage.get(conversation_id, [])
        
        try:
            ai_response = await chat_with_ai(
                request.message, 
                None,  # Use default model
                db,
                conversation_history=conversation_history
            )
            code_snippets = None  # Can be extracted from response if needed
        except Exception as e:
            logger.error(f"Chat failed: {str(e)}", exc_info=True)
            # Fallback response
            ai_response = "I apologize, but I encountered an error. Please try again or check your AI model configuration."
            code_snippets = None
        
        # Add assistant response to history
        conversation_storage[conversation_id].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
        return ChatResponse(
            message=ai_response,
            conversation_id=conversation_id,
            suggestions=None,
            code_snippets=code_snippets
        )
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/api/ai/chat/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    try:
        if conversation_id not in conversation_storage:
            return {"conversation_id": conversation_id, "messages": []}
        return {
            "conversation_id": conversation_id,
            "messages": conversation_storage[conversation_id]
        }
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation history: {str(e)}")

@app.post("/api/ai/suggestions")
async def get_suggestions(context: Optional[Dict] = None, db: Session = Depends(get_db)):
    """Get AI proactive strategy suggestions"""
    try:
        # Simplified suggestions - can be enhanced with more sophisticated logic
        suggestions = [
            "Consider a mean reversion strategy using Bollinger Bands",
            "Try a momentum strategy based on RSI indicators",
            "Explore a pairs trading strategy for correlated stocks"
        ]
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Failed to get suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

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

@app.get("/api/market/quotes", response_model=List[MarketQuote])
async def get_quotes(symbols: str):
    """
    Get real-time quotes for multiple symbols
    Query parameter: symbols (comma-separated, e.g., "AAPL,MSFT,GOOGL")
    Limited to 20 symbols per request to prevent overload
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Limit number of symbols per request
        if len(symbol_list) > 20:
            logger.warning(f"Too many symbols requested ({len(symbol_list)}), limiting to 20")
            symbol_list = symbol_list[:20]
        
        quotes = await get_multiple_quotes(symbol_list)
        return quotes
    except Exception as e:
        logger.error(f"Failed to get quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quotes: {str(e)}")

@app.get("/api/market/indicators/{symbol}")
async def get_indicators(symbol: str, indicators: str = "MACD,RSI,BB", period: int = 20):
    """
    Get technical indicators for a symbol
    Query parameters:
    - indicators: comma-separated indicator names (default: "MACD,RSI,BB")
    - period: period for calculations (default: 20)
    """
    try:
        indicator_list = [i.strip() for i in indicators.split(',')]
        data = await get_technical_indicators(symbol.upper(), indicator_list, period)
        # Convert DataFrame to dict for JSON response
        if hasattr(data, 'to_dict'):
            import numpy as np
            import pandas as pd
            # Replace NaN and Infinity with None for JSON compatibility
            data_clean = data.replace([np.inf, -np.inf], np.nan)
            data_clean = data_clean.where(pd.notnull(data_clean), None)
            return data_clean.to_dict(orient='records')
        return data
    except Exception as e:
        logger.error(f"Failed to get indicators for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get indicators: {str(e)}")

@app.get("/api/market/overview")
async def get_overview():
    """Get market overview data (cached for 30 seconds)"""
    try:
        # Use cache to reduce API calls
        from cachetools import TTLCache
        cache_key = "market_overview"
        
        if not hasattr(get_overview, '_cache'):
            get_overview._cache = TTLCache(maxsize=1, ttl=30)
        
        if cache_key in get_overview._cache:
            return get_overview._cache[cache_key]
        
        overview = await get_market_overview()
        get_overview._cache[cache_key] = overview
        return overview
    except Exception as e:
        logger.error(f"Failed to get market overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get market overview: {str(e)}")

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
    # #region agent log
    try:
        import os, json
        log_path = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"main.py:551","message":"get_ai_models endpoint called","data":{"path":"/api/ai-models"}})+'\n')
    except: pass
    # #endregion
    try:
        models = db.query(AIModelConfig).filter(AIModelConfig.is_active == True).all()
        result = []
        for model in models:
            # Handle provider enum conversion - SQLAlchemy may return string or enum
            # This handles the case where database stores 'custom' but SQLAlchemy expects CUSTOM
            provider_value = None
            try:
                if isinstance(model.provider, AIProvider):
                    # Already an enum, get its value
                    provider_value = model.provider.value
                elif isinstance(model.provider, str):
                    # It's a string from database, validate and use it
                    # Try to convert to enum first to validate
                    try:
                        provider_enum = AIProvider(model.provider.lower())
                        provider_value = provider_enum.value
                    except (ValueError, AttributeError):
                        # If conversion fails, use the string as-is (for backward compatibility)
                        logger.warning(f"Invalid provider value '{model.provider}' for model {model.id}, using as-is")
                        provider_value = model.provider.lower()
                elif hasattr(model.provider, 'value'):
                    # Has value attribute (enum-like object)
                    provider_value = model.provider.value
                else:
                    # Fallback: convert to string and lowercase
                    provider_str = str(model.provider)
                    try:
                        provider_enum = AIProvider(provider_str.lower())
                        provider_value = provider_enum.value
                    except (ValueError, AttributeError):
                        provider_value = provider_str.lower()
            except Exception as e:
                logger.warning(f"Error processing provider for model {model.id}: {str(e)}")
                # Fallback to string representation
                provider_value = str(model.provider).lower() if model.provider else 'custom'
            
            result.append(AIModelConfigResponse(
                id=model.id,
                name=model.name,
                provider=provider_value,
                model_name=model.model_name,
                base_url=model.base_url,
                is_default=model.is_default,
                is_active=model.is_active,
                created_at=model.created_at
            ))
        return result
    except Exception as e:
        logger.error(f"Error fetching AI models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI models: {str(e)}")

@app.post("/api/ai-models", response_model=AIModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_model(model: AIModelConfigCreate, db: Session = Depends(get_db)):
    """Create new AI model configuration"""
    try:
        from ai_service_factory import encrypt_api_key
        
        logger.info(f"Creating AI model: {model.name}, provider: {model.provider}")
        
        # Validate provider enum - handle both string and enum types
        try:
            if isinstance(model.provider, str):
                # Convert string to enum
                provider_enum = AIProvider(model.provider.lower())
            elif isinstance(model.provider, AIProvider):
                provider_enum = model.provider
            else:
                # Try to get value if it's an enum with value attribute
                provider_value = getattr(model.provider, 'value', str(model.provider))
                provider_enum = AIProvider(provider_value.lower())
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid provider: {model.provider}, type: {type(model.provider)}, error: {str(e)}")
            valid_providers = [p.value for p in AIProvider]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: {model.provider}. Must be one of: {valid_providers}"
            )
        
        # Encrypt API key
        try:
            encrypted_key = encrypt_api_key(model.api_key)
            logger.info("API key encrypted successfully")
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to encrypt API key: {str(e)}"
            )
        
        # Create database model
        db_model = AIModelConfig(
            name=model.name,
            provider=provider_enum,
            api_key=encrypted_key,
            base_url=model.base_url,
            model_name=model.model_name,
            is_default=False,
            is_active=True
        )
        
        # If this is set as default, unset others
        if hasattr(model, 'is_default') and model.is_default:
            db.query(AIModelConfig).update({"is_default": False})
            db_model.is_default = True
        
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        logger.info(f"AI model created successfully with ID: {db_model.id}")
        
        # Return response with proper serialization
        return {
            "id": db_model.id,
            "name": db_model.name,
            "provider": db_model.provider.value if hasattr(db_model.provider, 'value') else str(db_model.provider),
            "model_name": db_model.model_name,
            "base_url": db_model.base_url,
            "is_default": db_model.is_default,
            "is_active": db_model.is_active,
            "created_at": db_model.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating AI model: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create AI model: {str(e)}"
        )

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
    from ai_service_factory import test_ai_model_connection
    
    try:
        result = await test_ai_model_connection(model_id, db)
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

# Stock Pool endpoints
@app.get("/api/stock-pools", response_model=List[StockPoolSchema])
async def get_stock_pools(db: Session = Depends(get_db)):
    """Get all stock pools"""
    pools = db.query(StockPool).order_by(StockPool.created_at.desc()).all()
    return pools

@app.get("/api/stock-pools/{pool_id}", response_model=StockPoolSchema)
async def get_stock_pool(pool_id: int, db: Session = Depends(get_db)):
    """Get a specific stock pool"""
    pool = db.query(StockPool).filter(StockPool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    return pool

@app.post("/api/stock-pools", response_model=StockPoolSchema, status_code=status.HTTP_201_CREATED)
async def create_stock_pool(pool: StockPoolCreate, db: Session = Depends(get_db)):
    """Create a new stock pool"""
    db_pool = StockPool(**pool.dict())
    db.add(db_pool)
    db.commit()
    db.refresh(db_pool)
    return db_pool

@app.put("/api/stock-pools/{pool_id}", response_model=StockPoolSchema)
async def update_stock_pool(pool_id: int, pool: StockPoolUpdate, db: Session = Depends(get_db)):
    """Update a stock pool"""
    db_pool = db.query(StockPool).filter(StockPool.id == pool_id).first()
    if not db_pool:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    
    update_data = pool.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pool, field, value)
    
    db.commit()
    db.refresh(db_pool)
    return db_pool

@app.delete("/api/stock-pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_pool(pool_id: int, db: Session = Depends(get_db)):
    """Delete a stock pool"""
    db_pool = db.query(StockPool).filter(StockPool.id == pool_id).first()
    if not db_pool:
        raise HTTPException(status_code=404, detail="Stock pool not found")
    
    db.delete(db_pool)
    db.commit()
    return None

# Stock search endpoints
@app.get("/api/market/stocks/search")
async def search_stocks(q: str = "", limit: int = 50, db: Session = Depends(get_db)):
    """Search stocks (from database cache)"""
    query = db.query(StockInfo)
    
    if q:
        # Search by symbol or name
        search_term = f"%{q.upper()}%"
        query = query.filter(
            (StockInfo.symbol.like(search_term)) |
            (StockInfo.name.like(search_term))
        )
    
    stocks = query.limit(limit).all()
    
    # If not found in database, return empty list (frontend can fallback to API)
    return [StockInfoSchema.from_orm(s) for s in stocks]

@app.get("/api/market/stocks/{symbol}/info", response_model=StockInfoSchema)
async def get_stock_info(symbol: str, db: Session = Depends(get_db)):
    """Get stock detailed information"""
    stock = db.query(StockInfo).filter(StockInfo.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock info not found")
    return stock

# Data sync endpoints (admin)
@app.post("/api/admin/sync-data", response_model=DataSyncResponse)
async def trigger_data_sync(request: DataSyncRequest, db: Session = Depends(get_db)):
    """Manually trigger data synchronization (admin)"""
    from services.data_service import DataService
    
    try:
        records_added = 0
        symbols_processed = 0
        
        async with DataService(db=db) as data_service:
            for symbol in request.symbols:
                try:
                    data = await data_service.get_historical_data(
                        symbol=symbol,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        use_cache=False  # Force fetch from API
                    )
                    
                    if data is not None and not data.empty:
                        records_added += len(data)
                        symbols_processed += 1
                except Exception as e:
                    logger.error(f"Failed to sync {symbol}: {e}")
                    continue
        
        return DataSyncResponse(
            success=True,
            message=f"Synced {symbols_processed} symbols, added {records_added} records",
            symbols_processed=symbols_processed,
            records_added=records_added
        )
    except Exception as e:
        logger.error(f"Data sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data sync failed: {str(e)}")

# Rate limit monitoring endpoints (admin)
@app.get("/api/admin/rate-limit-status")
async def get_rate_limit_status():
    """Get rate limit status (admin monitoring)"""
    try:
        from services.rate_limiter import rate_limiter
        status = rate_limiter.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {str(e)}")

@app.post("/api/admin/reset-daily-limit")
async def reset_daily_limit():
    """Reset daily request count (admin, emergency use only)"""
    try:
        from services.rate_limiter import rate_limiter
        rate_limiter.reset_daily_count()
        return {"message": "Daily limit reset successfully", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to reset daily limit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset daily limit: {str(e)}")
