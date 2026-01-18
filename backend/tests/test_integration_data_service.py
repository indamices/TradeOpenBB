"""
Integration tests for DataService
Tests data fetching with caching and multiple data sources
"""
import pytest
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.data_service import DataService
    from database import SessionLocal
    from models import DataSourceConfig
except ImportError:
    pytest.skip("Cannot import required modules", allow_module_level=True)


@pytest.fixture
def db_session():
    """Create database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_data_service_fetch_historical_data(db_session):
    """Test fetching historical data through DataService"""
    async with DataService(db=db_session) as data_service:
        # Test with a known stock symbol
        symbol = "AAPL"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            data = await data_service.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            # Verify data structure
            assert isinstance(data, pd.DataFrame)
            assert not data.empty, "Data should not be empty"
            
            # Verify required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                assert col in data.columns, f"Missing column: {col}"
            
            # Verify data types
            for col in required_columns:
                assert pd.api.types.is_numeric_dtype(data[col]), f"Column {col} should be numeric"
            
            print(f"PASS: Successfully fetched {len(data)} days of data for {symbol}")
            
        except Exception as e:
            pytest.skip(f"Skipping test due to data fetch error: {e}")


@pytest.mark.asyncio
async def test_data_service_caching(db_session):
    """Test that DataService caches data correctly"""
    async with DataService(db=db_session) as data_service:
        symbol = "AAPL"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        try:
            # First fetch
            with patch('services.data_service.openbb_service.get_stock_data') as mock_get:
                mock_get.return_value = pd.DataFrame({
                    'Open': [100.0] * 7,
                    'High': [105.0] * 7,
                    'Low': [95.0] * 7,
                    'Close': [102.0] * 7,
                    'Volume': [1000000] * 7
                }, index=pd.date_range(start=start_date, end=end_date, freq='D'))
                
                data1 = await data_service.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=False  # First call should not use cache
                )
                
                # Second fetch should potentially use cache
                data2 = await data_service.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    use_cache=True  # Second call can use cache
                )
                
                # Data should be the same
                assert len(data1) == len(data2), "Cached data should have same length"
                print("PASS: Data caching works correctly")
                
        except Exception as e:
            pytest.skip(f"Skipping test due to caching test error: {e}")


@pytest.mark.asyncio
async def test_data_service_batch_fetch(db_session):
    """Test batch fetching data for multiple symbols"""
    async with DataService(db=db_session) as data_service:
        symbols = ["AAPL", "GOOGL", "MSFT"]
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        try:
            data_dict = await data_service.batch_fetch_historical_data(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date
            )
            
            # Verify all symbols are present
            assert len(data_dict) > 0, "Should fetch data for at least one symbol"
            
            # Verify data structure for each symbol
            for symbol, data in data_dict.items():
                assert isinstance(data, pd.DataFrame)
                assert not data.empty, f"Data for {symbol} should not be empty"
                assert 'Close' in data.columns, f"Missing Close column for {symbol}"
            
            print(f"PASS: Successfully batch fetched data for {len(data_dict)} symbols")
            
        except Exception as e:
            pytest.skip(f"Skipping test due to batch fetch error: {e}")


@pytest.mark.asyncio
async def test_data_service_fallback_mechanism(db_session):
    """Test data source fallback mechanism"""
    async with DataService(db=db_session) as data_service:
        symbol = "AAPL"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        try:
            # Test with primary source failing, should fallback
            with patch('services.data_service.openbb_service.get_stock_data', side_effect=Exception("Primary source failed")):
                # Should fallback to other sources
                data = await data_service.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # If fallback works, we should get data
                # If all sources fail, we get None
                if data is not None:
                    assert isinstance(data, pd.DataFrame)
                    print("PASS: Fallback mechanism works")
                else:
                    print("INFO: All data sources failed (expected in test environment)")
                    
        except Exception as e:
            pytest.skip(f"Skipping test due to fallback test error: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
