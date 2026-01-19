"""
Database configuration and session management
Supports both SQLite (default) and PostgreSQL

优化：
- SQLite: 使用 StaticPool（无需连接池）
- PostgreSQL: 优化的连接池配置（10 基础连接，20 额外连接，30秒超时，1小时回收）
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Support both PostgreSQL and SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL or it's empty, use SQLite
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./smartquant.db"
elif DATABASE_URL.startswith("sqlite"):
    # SQLite URL is already set
    pass
else:
    # PostgreSQL URL
    # Fix for Render: If using internal connection string (dpg-xxxxx-a), convert to external
    # Internal format: postgresql://user:pass@dpg-xxxxx-a/dbname
    # External format: postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname
    import re
    # Check if it's a Render internal connection string (contains dpg-xxxxx-a without domain)
    pattern = r'postgresql://([^@]+)@(dpg-[a-z0-9]+-a)(?:/|$)'
    match = re.search(pattern, DATABASE_URL)
    if match and '.render.com' not in DATABASE_URL and '.oregon-postgres' not in DATABASE_URL:
        # It's an internal connection string, try to convert to external
        # Extract credentials and database name
        credentials = match.group(1)
        hostname = match.group(2)
        # Try to extract database name
        db_match = re.search(r'@dpg-[a-z0-9]+-a(?:/|$)(.*?)(?:$|\?)', DATABASE_URL)
        db_name = db_match.group(1) if db_match else 'smartquant_db'
        # Construct external connection string
        external_url = f"postgresql://{credentials}@{hostname}.oregon-postgres.render.com/{db_name}"
        logger.warning(f"Detected Render internal connection string, attempting to use external format")
        logger.warning(f"Original: {DATABASE_URL[:50]}...")
        logger.warning(f"Using: {external_url[:50]}...")
        logger.warning("If connection still fails, manually set DATABASE_URL in Render Dashboard using External Connection String")
        DATABASE_URL = external_url

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration（不需要连接池）
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False,
        poolclass=StaticPool,  # SQLite 不需要连接池，使用 StaticPool
    )
else:
    # PostgreSQL configuration with optimized pool
    # 优化配置：
    # - pool_size=10: 基础连接池大小（从默认 5 增至 10）
    # - max_overflow=20: 额外连接数（从默认 10 增至 20）
    # - pool_timeout=30: 等待连接超时（秒）
    # - pool_recycle=3600: 1 小时回收连接（防止陈旧连接）
    # - pool_pre_ping=True: 使用前验证连接
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,          # 使用前验证连接
        pool_size=10,                # 基础连接池大小（从 5 增至 10）
        max_overflow=20,             # 额外连接数（从 10 增至 20）
        pool_timeout=30,             # 等待连接超时（秒）
        pool_recycle=3600,           # 1 小时回收连接（防止陈旧连接）
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and create default data"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Import here to avoid circular imports
    try:
        from . import models
        Base = models.Base
        Portfolio = models.Portfolio
        AIModelConfig = models.AIModelConfig
        AIProvider = models.AIProvider
        StockInfo = models.StockInfo
    except ImportError:
        from models import Base, Portfolio, AIModelConfig, AIProvider, StockInfo
    
    # Create all tables (including new ones) - with error handling
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/updated successfully")
        
        # Verify critical tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['portfolios', 'ai_model_configs', 'stock_info', 'strategies', 
                          'positions', 'orders', 'stock_pools', 'conversations']
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            logger.warning(f"Some tables may not have been created: {missing_tables}")
            # Try creating them individually
            for table_name in missing_tables:
                try:
                    # Get the table from Base metadata
                    table = Base.metadata.tables.get(table_name)
                    if table:
                        table.create(bind=engine, checkfirst=True)
                        logger.info(f"Created table: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to create table {table_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise  # Re-raise to prevent app from starting with invalid database
    
    # Create default portfolio with id=1 if it doesn't exist
    db = SessionLocal()
    try:
        # Check if portfolio with id=1 exists
        portfolio_1 = db.query(Portfolio).filter(Portfolio.id == 1).first()
        if not portfolio_1:
            # Create default portfolio with id=1
            default_portfolio = Portfolio(
                id=1,  # Explicitly set id=1
                name="Default Portfolio",
                initial_cash=100000.0,
                current_cash=100000.0,
                total_value=100000.0,
                daily_pnl=0.0,
                daily_pnl_percent=0.0
            )
            db.add(default_portfolio)
            db.commit()
            db.refresh(default_portfolio)
            logger.info(f"Created default portfolio with ID: {default_portfolio.id}")
        else:
            # Update existing portfolio to ensure consistent name for tests
            portfolio_1.name = "Default Portfolio"
            db.commit()
            logger.info(f"Default portfolio (ID=1) already exists, updated name to 'Default Portfolio'")
        
        # Create default AI models if they don't exist
        try:
            try:
                from .ai_service_factory import encrypt_api_key
            except ImportError:
                from ai_service_factory import encrypt_api_key
            
            # DeepSeek Chat model
            deepseek_model = db.query(AIModelConfig).filter(
                AIModelConfig.name == "DeepSeek Chat"
            ).first()
            if not deepseek_model:
                deepseek_api_key = "sk-f885af006ab149aea0c9759ecc34c9c2"
                encrypted_deepseek_key = encrypt_api_key(deepseek_api_key)
                deepseek_model = AIModelConfig(
                    name="DeepSeek Chat",
                    provider=AIProvider.OPENAI,
                    api_key=encrypted_deepseek_key,
                    base_url="https://api.deepseek.com/v1",
                    model_name="deepseek-chat",
                    is_default=True,  # Set as default
                    is_active=True  # Set as active (only one should be active)
                )
                db.add(deepseek_model)
                logger.info("Created default DeepSeek Chat model")
            else:
                logger.info("DeepSeek Chat model already exists")
            
            # GLM-4.7 model
            glm_model = db.query(AIModelConfig).filter(
                AIModelConfig.name == "GLM-4.7"
            ).first()
            if not glm_model:
                glm_api_key = "35d69764ebc34827b75b1fe275e1a440.63KnzOkYt5kgUZfp"
                encrypted_glm_key = encrypt_api_key(glm_api_key)
                glm_model = AIModelConfig(
                    name="GLM-4.7",
                    provider=AIProvider.OPENAI,
                    api_key=encrypted_glm_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4",  # 智谱AI API endpoint
                    model_name="glm-4",  # GLM-4.7 使用 glm-4 作为模型名
                    is_default=False,  # DeepSeek is default
                    is_active=True  # Set as active so it shows up in the UI
                )
                db.add(glm_model)
                db.flush()  # Flush to get the ID
                logger.info("Created default GLM-4.7 model")
            else:
                logger.info("GLM-4.7 model already exists")
            
            # Ensure only one default model exists (keep is_default for backward compatibility)
            default_models = db.query(AIModelConfig).filter(
                AIModelConfig.is_default == True
            ).all()
            if len(default_models) > 1:
                # Keep DeepSeek as default, unset others
                for model in default_models:
                    if model.name != "DeepSeek Chat":
                        model.is_default = False
                logger.info("Fixed multiple default models, keeping DeepSeek Chat as default")
            
            # CRITICAL: Ensure only one active model exists (use is_active to control current model)
            active_models = db.query(AIModelConfig).filter(
                AIModelConfig.is_active == True
            ).all()
            if len(active_models) > 1:
                # Keep DeepSeek as active, deactivate others
                for model in active_models:
                    if model.name != "DeepSeek Chat":
                        model.is_active = False
                logger.info("Fixed multiple active models, keeping DeepSeek Chat as active")
            elif len(active_models) == 0:
                # If no active model, activate DeepSeek
                if deepseek_model:
                    deepseek_model.is_active = True
                    logger.info("No active model found, activated DeepSeek Chat")
            else:
                # At least one model is active, ensure DeepSeek is active if it exists
                deepseek_active = any(m.name == "DeepSeek Chat" and m.is_active for m in active_models)
                if deepseek_model and not deepseek_active:
                    # Deactivate all, activate DeepSeek
                    for model in active_models:
                        model.is_active = False
                    deepseek_model.is_active = True
                    logger.info("Ensured DeepSeek Chat is the active model")
            
            # Ensure both models exist and have correct status
            all_models = db.query(AIModelConfig).all()
            deepseek_exists = any(m.name == "DeepSeek Chat" for m in all_models)
            glm_exists = any(m.name == "GLM-4.7" for m in all_models)
            
            if not deepseek_exists:
                logger.warning("DeepSeek Chat model not found after initialization")
            if not glm_exists:
                logger.warning("GLM-4.7 model not found after initialization")
            
            logger.info(f"Initialized AI models: DeepSeek Chat (exists: {deepseek_exists}), GLM-4.7 (exists: {glm_exists})")
            
            db.commit()
        except Exception as e:
            logger.error(f"Error creating default AI models: {str(e)}", exc_info=True)
            db.rollback()
            # Don't raise here - allow app to start even if AI models fail to initialize
            # They can be added manually later
        
    except Exception as e:
        logger.error(f"Error creating default portfolio: {str(e)}", exc_info=True)
        db.rollback()
        raise  # Re-raise to prevent app from starting with invalid state
    finally:
        db.close()
