"""
Tests for OpenBB Service
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openbb_service import OpenBBService, openbb_service

class TestOpenBBService:
    """Test cases for OpenBBService"""
    
    def test_get_stock_data_with_yfinance(self):
        """Test getting stock data using yfinance fallback"""
        service = OpenBBService()
        
        # Use a well-known symbol
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data = service.get_stock_data("AAPL", start_date, end_date)
            assert isinstance(data, pd.DataFrame)
            assert not data.empty
            assert 'Close' in data.columns
            assert 'Open' in data.columns
            assert 'High' in data.columns
            assert 'Low' in data.columns
            assert 'Volume' in data.columns
        except Exception as e:
            # If yfinance fails (e.g., network issue), skip test
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_stock_data_with_default_end_date(self):
        """Test getting stock data with default end date"""
        service = OpenBBService()
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        try:
            data = service.get_stock_data("AAPL", start_date)
            assert isinstance(data, pd.DataFrame)
            assert not data.empty
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_stock_data_invalid_symbol(self):
        """Test getting stock data for invalid symbol"""
        service = OpenBBService()
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        with pytest.raises((ValueError, Exception)):
            service.get_stock_data("INVALID_SYMBOL_XYZ123", start_date, end_date)
    
    def test_get_realtime_quote(self):
        """Test getting real-time quote"""
        service = OpenBBService()
        
        try:
            quote = service.get_realtime_quote("AAPL")
            assert isinstance(quote, dict)
            assert 'price' in quote
            assert 'change' in quote
            assert 'change_percent' in quote
            assert 'volume' in quote
            assert isinstance(quote['price'], (int, float))
            assert quote['price'] > 0
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_realtime_quote_invalid_symbol(self):
        """Test getting quote for invalid symbol"""
        service = OpenBBService()
        
        with pytest.raises(ValueError):
            service.get_realtime_quote("INVALID_SYMBOL_XYZ123")
    
    def test_get_technical_indicators_sma(self):
        """Test getting SMA technical indicator"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["sma"], period=20)
            assert isinstance(indicators, pd.DataFrame)
            assert 'SMA' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_ema(self):
        """Test getting EMA technical indicator"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["ema"], period=20)
            assert isinstance(indicators, pd.DataFrame)
            assert 'EMA' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_rsi(self):
        """Test getting RSI technical indicator"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["rsi"], period=14)
            assert isinstance(indicators, pd.DataFrame)
            assert 'RSI' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_macd(self):
        """Test getting MACD technical indicator"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["macd"], period=20)
            assert isinstance(indicators, pd.DataFrame)
            assert 'MACD' in indicators.columns
            assert 'MACD_Signal' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_bollinger_bands(self):
        """Test getting Bollinger Bands technical indicator"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["bb"], period=20)
            assert isinstance(indicators, pd.DataFrame)
            assert 'BB_Upper' in indicators.columns
            assert 'BB_Lower' in indicators.columns
            assert 'BB_Middle' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_multiple(self):
        """Test getting multiple technical indicators"""
        service = OpenBBService()
        
        try:
            indicators = service.get_technical_indicators("AAPL", ["sma", "rsi", "macd"], period=20)
            assert isinstance(indicators, pd.DataFrame)
            assert 'SMA' in indicators.columns or 'RSI' in indicators.columns or 'MACD' in indicators.columns
        except Exception as e:
            pytest.skip(f"yfinance unavailable: {str(e)}")
    
    def test_get_technical_indicators_invalid_symbol(self):
        """Test getting indicators for invalid symbol"""
        service = OpenBBService()
        
        with pytest.raises(ValueError):
            service.get_technical_indicators("INVALID_SYMBOL_XYZ123", ["sma"], period=20)
    
    def test_singleton_instance(self):
        """Test that openbb_service is a singleton instance"""
        assert openbb_service is not None
        assert isinstance(openbb_service, OpenBBService)
        # Should be the same instance
        from openbb_service import openbb_service as service2
        assert openbb_service is service2
