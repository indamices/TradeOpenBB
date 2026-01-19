#!/usr/bin/env python3
"""
Test setup helper script for CI/CD environments

This script generates proper environment configuration for testing,
including valid Fernet encryption keys and database initialization.
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_encryption_key() -> str:
    """Generate a valid Fernet encryption key (44 chars base64-url-safe encoded)"""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    logger.info(f"Generated encryption key: {key}")
    return key


def setup_env_file(backend_dir: Path, encryption_key: str):
    """Create or update .env file with proper configuration"""
    env_file = backend_dir / ".env"

    # Write environment variables
    env_content = f"""# Auto-generated test environment configuration
DATABASE_URL=sqlite:///./test.db
ENCRYPTION_KEY={encryption_key}
ENVIRONMENT=test
# Optional: Override with your API keys for testing
# API_KEY=your_api_key_here
# GEMINI_API_KEY=your_gemini_key_here
"""

    with open(env_file, 'w') as f:
        f.write(env_content)

    logger.info(f"Created .env file at {env_file}")
    logger.info("Configuration:")
    print(env_content)


def initialize_database(backend_dir: Path):
    """Initialize the database with proper error handling"""
    # Change to backend directory
    original_dir = os.getcwd()
    os.chdir(backend_dir)

    try:
        # Import after changing directory
        from database import init_db

        init_db()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Tests will attempt to create tables automatically")
        return False
    finally:
        os.chdir(original_dir)


def main():
    """Main setup function"""
    # Get backend directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir / "backend"

    if not backend_dir.exists():
        logger.error(f"Backend directory not found: {backend_dir}")
        sys.exit(1)

    logger.info("Setting up test environment...")
    logger.info(f"Backend directory: {backend_dir}")

    # Step 1: Generate encryption key
    encryption_key = generate_encryption_key()

    # Step 2: Setup .env file
    setup_env_file(backend_dir, encryption_key)

    # Step 3: Initialize database
    initialize_database(backend_dir)

    logger.info("\n" + "="*50)
    logger.info("Test environment setup complete!")
    logger.info("="*50)
    logger.info("\nYou can now run tests with:")
    logger.info(f"  cd {backend_dir}")
    logger.info("  pytest tests/ -v")
    logger.info("\nOr use the simple test runner:")
    logger.info(f"  cd {backend_dir}")
    logger.info("  python run_tests_simple.py")


if __name__ == "__main__":
    main()
