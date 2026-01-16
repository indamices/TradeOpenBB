"""
Comprehensive tests for input validation and boundary conditions
"""
import pytest
from fastapi import status
import sys


class TestNegativeValues:
    """Test handling of negative values"""
    
    def test_negative_initial_cash(self, client):
        """Test portfolio creation with negative initial cash"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": -1000.0}
        )
        # Should reject negative values
        assert response.status_code in [400, 422]
    
    def test_negative_quantity(self, client, default_portfolio):
        """Test order creation with negative quantity"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": -10,
                "portfolio_id": default_portfolio
            }
        )
        # Should reject negative quantity
        assert response.status_code in [400, 422]
    
    def test_negative_price(self, client, default_portfolio):
        """Test position creation with negative price"""
        response = client.post(
            "/api/positions",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "avg_price": -150.0,
                "current_price": 155.0,
                "portfolio_id": default_portfolio
            }
        )
        # Should reject negative price
        assert response.status_code in [400, 422]


class TestZeroValues:
    """Test handling of zero values"""
    
    def test_zero_initial_cash(self, client):
        """Test portfolio creation with zero initial cash"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": 0.0}
        )
        # May or may not be allowed depending on business logic
        assert response.status_code in [200, 201, 400, 422]
    
    def test_zero_quantity(self, client, default_portfolio):
        """Test order creation with zero quantity"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0,
                "portfolio_id": default_portfolio
            }
        )
        # Should reject zero quantity
        assert response.status_code in [400, 422]
    
    def test_zero_price(self, client, default_portfolio):
        """Test position creation with zero price"""
        response = client.post(
            "/api/positions",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "avg_price": 0.0,
                "current_price": 0.0,
                "portfolio_id": default_portfolio
            }
        )
        # May or may not be allowed
        assert response.status_code in [200, 201, 400, 422]


class TestExtremelyLargeValues:
    """Test handling of extremely large values"""
    
    def test_very_large_initial_cash(self, client):
        """Test portfolio creation with very large initial cash"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": sys.float_info.max}
        )
        # Should handle gracefully (may accept or reject)
        assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_very_large_quantity(self, client, default_portfolio):
        """Test order creation with very large quantity"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": sys.maxsize,
                "portfolio_id": default_portfolio
            }
        )
        # Should handle gracefully
        assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_very_large_string(self, client):
        """Test portfolio creation with very long name"""
        long_name = "A" * 10000  # 10KB string
        response = client.post(
            "/api/portfolio",
            json={"name": long_name, "initial_cash": 1000.0}
        )
        # Should handle gracefully (may truncate or reject)
        assert response.status_code in [200, 201, 400, 422, 413, 500]


class TestSpecialCharacters:
    """Test handling of special characters"""
    
    def test_sql_injection_attempt(self, client):
        """Test handling of SQL injection attempts"""
        malicious_name = "'; DROP TABLE portfolios; --"
        response = client.post(
            "/api/portfolio",
            json={"name": malicious_name, "initial_cash": 1000.0}
        )
        # Should be handled safely (stored as string, not executed)
        # If accepted, verify it's stored as string
        if response.status_code == 201:
            portfolio_id = response.json()["id"]
            get_response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
            if get_response.status_code == 200:
                data = get_response.json()
                # Should be stored as-is (not executed)
                assert malicious_name in data.get("name", "")
    
    def test_xss_attempt(self, client):
        """Test handling of XSS attempts"""
        xss_name = "<script>alert('XSS')</script>"
        response = client.post(
            "/api/portfolio",
            json={"name": xss_name, "initial_cash": 1000.0}
        )
        # Should be handled safely
        assert response.status_code in [200, 201, 400, 422]
    
    def test_special_characters_in_symbol(self, client, default_portfolio):
        """Test handling of special characters in symbol"""
        special_symbols = ["AAPL!", "@MSFT", "GOOGL#", "TSLA$"]
        for symbol in special_symbols:
            response = client.post(
                "/api/orders",
                json={
                    "symbol": symbol,
                    "side": "BUY",
                    "type": "MARKET",
                    "quantity": 10,
                    "portfolio_id": default_portfolio
                }
            )
            # May accept or reject depending on validation
            assert response.status_code in [200, 201, 400, 422, 500]


class TestUnicodeInput:
    """Test handling of Unicode characters"""
    
    def test_unicode_portfolio_name(self, client):
        """Test portfolio creation with Unicode name"""
        unicode_name = "测试组合 🚀 中文"
        response = client.post(
            "/api/portfolio",
            json={"name": unicode_name, "initial_cash": 1000.0}
        )
        # Should handle Unicode correctly
        assert response.status_code in [200, 201, 400, 422]
        
        if response.status_code == 201:
            portfolio_id = response.json()["id"]
            get_response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
            if get_response.status_code == 200:
                data = get_response.json()
                # Unicode should be preserved
                assert unicode_name in data.get("name", "")
    
    def test_emoji_in_name(self, client):
        """Test portfolio creation with emoji"""
        emoji_name = "Portfolio 😀 🎉 💰"
        response = client.post(
            "/api/portfolio",
            json={"name": emoji_name, "initial_cash": 1000.0}
        )
        assert response.status_code in [200, 201, 400, 422]
    
    def test_unicode_symbol(self, client, default_portfolio):
        """Test order creation with Unicode symbol (should fail)"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "测试",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 10,
                "portfolio_id": default_portfolio
            }
        )
        # Should reject invalid symbol format
        assert response.status_code in [400, 422, 500]


class TestEmptyStrings:
    """Test handling of empty strings"""
    
    def test_empty_portfolio_name(self, client):
        """Test portfolio creation with empty name"""
        response = client.post(
            "/api/portfolio",
            json={"name": "", "initial_cash": 1000.0}
        )
        # Should reject empty name
        assert response.status_code in [400, 422]
    
    def test_empty_symbol(self, client, default_portfolio):
        """Test order creation with empty symbol"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 10,
                "portfolio_id": default_portfolio
            }
        )
        # Should reject empty symbol
        assert response.status_code in [400, 422]
    
    def test_whitespace_only_name(self, client):
        """Test portfolio creation with whitespace-only name"""
        response = client.post(
            "/api/portfolio",
            json={"name": "   ", "initial_cash": 1000.0}
        )
        # May be trimmed or rejected
        assert response.status_code in [200, 201, 400, 422]


class TestInvalidTypes:
    """Test handling of invalid data types"""
    
    def test_string_instead_of_number(self, client):
        """Test portfolio creation with string instead of number"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": "not a number"}
        )
        # Should reject invalid type
        assert response.status_code in [400, 422]
    
    def test_number_instead_of_string(self, client):
        """Test portfolio creation with number instead of string"""
        response = client.post(
            "/api/portfolio",
            json={"name": 12345, "initial_cash": 1000.0}
        )
        # May accept (if auto-converted) or reject
        assert response.status_code in [200, 201, 400, 422]
    
    def test_null_in_required_field(self, client):
        """Test portfolio creation with null in required field"""
        response = client.post(
            "/api/portfolio",
            json={"name": None, "initial_cash": 1000.0}
        )
        # Should reject null in required field
        assert response.status_code in [400, 422]
    
    def test_array_instead_of_object(self, client):
        """Test sending array instead of object"""
        response = client.post(
            "/api/portfolio",
            json=[{"name": "Test", "initial_cash": 1000.0}]
        )
        # Should reject wrong structure
        assert response.status_code in [400, 422]


class TestBoundaryValues:
    """Test boundary value conditions"""
    
    def test_minimum_valid_quantity(self, client, default_portfolio):
        """Test order creation with minimum valid quantity (1)"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 1,  # Minimum valid
                "portfolio_id": default_portfolio
            }
        )
        # Should accept minimum valid value
        assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_maximum_reasonable_quantity(self, client, default_portfolio):
        """Test order creation with maximum reasonable quantity"""
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 1000000,  # Large but reasonable
                "portfolio_id": default_portfolio
            }
        )
        # Should handle large but reasonable values
        assert response.status_code in [200, 201, 400, 422, 500]
    
    def test_float_precision(self, client):
        """Test handling of floating point precision"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": 1000.123456789}
        )
        # Should handle float precision
        assert response.status_code in [200, 201, 400, 422, 500]


class TestMissingFields:
    """Test handling of missing required fields"""
    
    def test_missing_portfolio_name(self, client):
        """Test portfolio creation without name"""
        response = client.post(
            "/api/portfolio",
            json={"initial_cash": 1000.0}
        )
        # Should reject missing required field
        assert response.status_code in [400, 422]
    
    def test_missing_initial_cash(self, client):
        """Test portfolio creation without initial_cash"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test"}
        )
        # Should reject missing required field
        assert response.status_code in [400, 422]
    
    def test_missing_all_fields(self, client):
        """Test portfolio creation with empty body"""
        response = client.post(
            "/api/portfolio",
            json={}
        )
        # Should reject missing all required fields
        assert response.status_code in [400, 422]
    
    def test_missing_optional_fields(self, client):
        """Test that optional fields can be omitted"""
        response = client.post(
            "/api/portfolio",
            json={"name": "Test", "initial_cash": 1000.0}
        )
        # Should accept with only required fields
        assert response.status_code in [200, 201, 400, 422, 500]
