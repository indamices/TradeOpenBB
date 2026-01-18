"""
Unit tests for Futu service
Note: These tests require futu library to be mocked or installed
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Mock futu library for testing
try:
    import futu as ft
    FUTU_AVAILABLE_FOR_TEST = True
except ImportError:
    FUTU_AVAILABLE_FOR_TEST = False

class MockFutu:
    class Market:
        US = "US"
        HK = "HK"
        SH = "SH"
        SZ = "SZ"
    
    class KLType:
        K_DAY = "K_DAY"
    
    class AuType:
        QFQ = "QFQ"
    
    class KL_FIELD:
        ALL = ["time_key", "open", "high", "low", "close", "volume"]
    
    class CapitalFlowPeriod:
        DAY = "DAY"
    
    class RET_OK:
        pass
    
    RET_OK = "OK"
    
    class OpenQuoteContext:
        def __init__(self, host, port):
            self.host = host
            self.port = port
        
        def request_history_kline(self, code, start, end, ktype, autype, fields, max_count):
            # Return mock data
            data = pd.DataFrame({
                'time_key': pd.date_range(start=start, end=end, freq='D'),
                'open': [100.0] * 10,
                'high': [105.0] * 10,
                'low': [95.0] * 10,
                'close': [102.0] * 10,
                'volume': [1000000] * 10
            })
            return MockFutu.RET_OK, data, None
        
        def get_market_snapshot(self, codes):
            data = pd.DataFrame({
                'code': codes,
                'last_price': [102.0],
                'change_val': [2.0],
                'change_rate': [0.02],
                'volume': [1000000],
                'high_price': [105.0],
                'low_price': [95.0],
                'open_price': [100.0],
                'prev_close_price': [100.0]
            })
            return MockFutu.RET_OK, data
        
        def get_capital_flow(self, code, period):
            data = pd.DataFrame({
                'in_flow': [1000000],
                'out_flow': [800000],
                'net_flow': [200000],
                'large_in': [500000],
                'large_out': [400000],
                'medium_in': [300000],
                'medium_out': [200000],
                'small_in': [200000],
                'small_out': [200000]
            })
            return MockFutu.RET_OK, data
        
        def close(self):
            pass


@pytest.fixture
def mock_futu():
    """Mock futu library"""
    with patch.dict('sys.modules', {'futu': MockFutu}):
        # Reload the module to use mocked futu
        import importlib
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            import futu_service as futu_service_module
        except ImportError:
            # Skip if cannot import
            pytest.skip("Cannot import futu_service module")
        
        importlib.reload(futu_service_module)
        yield MockFutu


@pytest.fixture
def futu_service(mock_futu):
    """Create Futu service instance with mocked library"""
    # Skip if futu is not available and mocking fails
    if not FUTU_AVAILABLE_FOR_TEST:
        pytest.skip("Futu library not available")
    
    try:
        from futu_service import FutuService
    except ImportError:
        # Try without backend prefix
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from futu_service import FutuService
    
    with patch('futu_service.FUTU_AVAILABLE', True):
        service = FutuService(host='127.0.0.1', port=11111)
        yield service


class TestFutuServiceInitialization:
    """Test Futu service initialization"""
    
    def test_init(self, mock_futu):
        """Test service initialization"""
        if not FUTU_AVAILABLE_FOR_TEST:
            pytest.skip("Futu library not available")
        
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            from futu_service import FutuService
        except ImportError:
            pytest.skip("Cannot import FutuService")
        
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            assert service.host == '127.0.0.1'
            assert service.port == 11111
    
    def test_get_market_us(self, mock_futu):
        """Test market detection for US stocks"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from futu_service import FutuService
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            market = service._get_market('AAPL')
            assert market == "US" or market == "US"  # May return string or enum
    
    def test_get_market_hk(self, mock_futu):
        """Test market detection for HK stocks"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from futu_service import FutuService
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            market = service._get_market('00700.HK')
            assert market == "HK" or (hasattr(market, 'value') and market.value == "HK")
    
    def test_get_market_sh(self, mock_futu):
        """Test market detection for Shanghai stocks"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from futu_service import FutuService
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            market = service._get_market('000001.SH')
            assert market == "SH" or (hasattr(market, 'value') and market.value == "SH")
    
    def test_get_market_sz(self, mock_futu):
        """Test market detection for Shenzhen stocks"""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from futu_service import FutuService
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            market = service._get_market('000001.SZ')
            assert market == "SZ" or (hasattr(market, 'value') and market.value == "SZ")


class TestDataFetching:
    """Test data fetching functionality"""
    
    def test_get_stock_data(self, futu_service, mock_futu):
        """Test getting stock data"""
        df = futu_service.get_stock_data('AAPL', '2023-01-01', '2023-01-10')
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
        assert 'Volume' in df.columns
    
    def test_get_realtime_quote(self, futu_service, mock_futu):
        """Test getting realtime quote"""
        quote = futu_service.get_realtime_quote('AAPL')
        
        assert 'price' in quote
        assert 'change' in quote
        assert 'change_percent' in quote
        assert 'volume' in quote
        assert quote['price'] == 102.0
    
    def test_get_capital_flow(self, futu_service, mock_futu):
        """Test getting capital flow"""
        flow = futu_service.get_capital_flow('AAPL', 'day')
        
        assert 'in_flow' in flow
        assert 'out_flow' in flow
        assert 'net_flow' in flow
        assert flow['net_flow'] == 200000


class TestAvailability:
    """Test service availability checks"""
    
    def test_is_available_static_true(self, mock_futu):
        """Test static availability check when library is available"""
        if not FUTU_AVAILABLE_FOR_TEST:
            pytest.skip("Futu library not available")
        
        try:
            from futu_service import FutuService
        except ImportError:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from futu_service import FutuService
        
        with patch('futu_service.FUTU_AVAILABLE', True):
            assert FutuService.is_available_static() is True
    
    def test_is_available_static_false(self):
        """Test static availability check when library is not available"""
        from futu_service import FutuService
        with patch('futu_service.FUTU_AVAILABLE', False):
            assert FutuService.is_available_static() is False
    
    def test_is_available_connected(self, futu_service, mock_futu):
        """Test availability when connected"""
        if not FUTU_AVAILABLE_FOR_TEST:
            pytest.skip("Futu library not available")
        
        # Mock successful connection
        futu_service.quote_ctx = Mock()
        assert futu_service.is_available() is True
    
    def test_is_available_not_connected(self):
        """Test availability when not connected"""
        try:
            from futu_service import FutuService
        except ImportError:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from futu_service import FutuService
        
        with patch('futu_service.FUTU_AVAILABLE', True):
            service = FutuService()
            # Connection will fail in test environment
            with patch.object(service, '_ensure_connected', side_effect=Exception("Connection failed")):
                assert service.is_available() is False


class TestContextManager:
    """Test context manager functionality"""
    
    def test_context_manager(self, futu_service, mock_futu):
        """Test using service as context manager"""
        with futu_service as service:
            assert service.quote_ctx is not None
        
        # Connection should be closed
        assert futu_service.quote_ctx is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
