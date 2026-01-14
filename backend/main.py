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

# Use absolute imports for Docker deployment
from database import get_db, init_db
from models import Portfolio, Position, Order, Strategy, AIModelConfig, OrderSide, OrderType, OrderStatus, AIProvider, Base
from schemas import (
    Portfolio as PortfolioSchema, PortfolioCreate, PortfolioUpdate,
    Position as PositionSchema, PositionCreate, PositionUpdate,
    Order as OrderSchema, OrderCreate, OrderUpdate,
    Strategy as StrategySchema, StrategyCreate, StrategyUpdate,
    MarketQuote, StrategyGenerationRequest, StrategyGenerationResponse,
    AIModelConfigCreate, AIModelConfigUpdate, AIModelConfigResponse,
    BacktestRequest, BacktestResult, ChatRequest, ChatResponse
)
from market_service import get_realtime_quote, get_multiple_quotes, get_market_overview, get_technical_indicators
from ai_service_factory import generate_strategy
from backtest_engine import run_backtest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory conversation storage (in production, use database)
conversation_storage: Dict[str, List[Dict]] = {}

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
    return response

# CORS middleware
# Allow local development and cloud platform domains
# Use allow_origin_regex for pattern matching to support wildcard domains
import re
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "https://tradeopenbb-frontend.onrender.com",  # Render frontend
    ],
    allow_origin_regex=r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
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

# AI Chat endpoints
@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """AI chat conversation"""
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
        
        # Generate response using strategy generation (simplified - can be enhanced)
        # For now, treat chat as strategy generation with context
        try:
            result = await generate_strategy(request.message, None, db)
            ai_response = result.explanation
            code_snippets = {'python': result.code} if result.code else None
        except Exception:
            # Fallback response
            ai_response = "I understand your question. Let me help you with strategy development."
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
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
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
            return data.to_dict(orient='records')
        return data
    except Exception as e:
        logger.error(f"Failed to get indicators for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get indicators: {str(e)}")

@app.get("/api/market/overview")
async def get_overview():
    """Get market overview data"""
    try:
        overview = await get_market_overview()
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
