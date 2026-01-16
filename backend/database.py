"""
Database configuration and session management
Supports both SQLite (default) and PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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
    except ImportError:
        from models import Base, Portfolio, AIModelConfig, AIProvider
    
    # Create all tables (including new ones)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/updated successfully")
    
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
            logger.info(f"Default portfolio (ID=1) already exists")
        
        # Create default AI models if they don't exist
        try:
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
                    is_active=True
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
                    is_active=True
                )
                db.add(glm_model)
                logger.info("Created default GLM-4.7 model")
            else:
                logger.info("GLM-4.7 model already exists")
            
            # Ensure only one default model exists
            default_models = db.query(AIModelConfig).filter(
                AIModelConfig.is_default == True
            ).all()
            if len(default_models) > 1:
                # Keep DeepSeek as default, unset others
                for model in default_models:
                    if model.name != "DeepSeek Chat":
                        model.is_default = False
                logger.info("Fixed multiple default models, keeping DeepSeek Chat as default")
            
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
