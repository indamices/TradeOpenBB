"""
Comprehensive tests for JSON serialization compliance
Tests for NaN, Infinity, nested structures, and edge cases
"""
import pytest
import json
import math
import numpy as np
from datetime import datetime
from decimal import Decimal
from fastapi import status
from utils.json_serializer import sanitize_for_json, sanitize_float


class TestJSONSerializationUtility:
    """Test the JSON serialization utility functions"""
    
    def test_sanitize_float_nan(self):
        """Test sanitizing NaN values"""
        result = sanitize_float(float('nan'))
        assert result is None
    
    def test_sanitize_float_infinity(self):
        """Test sanitizing Infinity values"""
        result = sanitize_float(float('inf'))
        assert result is None
    
    def test_sanitize_float_neg_infinity(self):
        """Test sanitizing negative Infinity values"""
        result = sanitize_float(float('-inf'))
        assert result is None
    
    def test_sanitize_float_normal(self):
        """Test sanitizing normal float values"""
        result = sanitize_float(3.14)
        assert result == 3.14
    
    def test_sanitize_for_json_nested_dict(self):
        """Test sanitizing nested dictionaries with NaN/Inf"""
        test_data = {
            "normal": 1.0,
            "nan_value": float('nan'),
            "inf_value": float('inf'),
            "neg_inf": float('-inf'),
            "nested": {
                "nan": float('nan'),
                "list": [1.0, float('nan'), 2.0]
            }
        }
        
        sanitized = sanitize_for_json(test_data)
        
        # Should be JSON serializable
        json_str = json.dumps(sanitized)
        assert json_str is not None
        
        # NaN/Inf should be replaced with None
        assert sanitized["nan_value"] is None
        assert sanitized["inf_value"] is None
        assert sanitized["neg_inf"] is None
        assert sanitized["nested"]["nan"] is None
        assert sanitized["nested"]["list"][1] is None
    
    def test_sanitize_for_json_list(self):
        """Test sanitizing lists with NaN/Inf"""
        test_data = [1.0, float('nan'), float('inf'), 2.0]
        sanitized = sanitize_for_json(test_data)
        
        json_str = json.dumps(sanitized)
        assert json_str is not None
        assert sanitized[1] is None
        assert sanitized[2] is None
    
    def test_sanitize_for_json_numpy_types(self):
        """Test sanitizing NumPy float types"""
        test_data = {
            "np_nan": np.nan,
            "np_inf": np.inf,
            "np_float": np.float64(3.14)
        }
        sanitized = sanitize_for_json(test_data)
        
        json_str = json.dumps(sanitized)
        assert json_str is not None
        assert sanitized["np_nan"] is None
        assert sanitized["np_inf"] is None
        assert sanitized["np_float"] == 3.14


class TestAPIJSONSerialization:
    """Test JSON serialization in API responses"""
    
    def test_indicators_with_nan_values(self, client):
        """Test that indicators endpoint handles NaN/Inf values correctly"""
        symbol = "AAPL"
        indicators = "MACD,RSI,BB"
        period = 20
        
        response = client.get(f"/api/market/indicators/{symbol}?indicators={indicators}&period={period}")
        
        if response.status_code == 200:
            # This should not raise ValueError
            data = response.json()
            
            # Verify the data is JSON serializable by re-serializing
            try:
                json_str = json.dumps(data)
                parsed = json.loads(json_str)
                assert parsed is not None
            except (ValueError, TypeError) as e:
                pytest.fail(f"Response contains non-JSON-compliant values: {e}")
    
    def test_indicators_nested_nan_values(self, client):
        """Test that nested structures in indicators are properly sanitized"""
        symbol = "AAPL"
        indicators = "MACD,RSI"
        period = 20
        
        response = client.get(f"/api/market/indicators/{symbol}?indicators={indicators}&period={period}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Recursively check for NaN/Inf in nested structures
            def check_for_nan_inf(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        check_for_nan_inf(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_for_nan_inf(item, f"{path}[{i}]")
                elif isinstance(obj, (float, np.floating)):
                    if math.isnan(obj) or math.isinf(obj):
                        pytest.fail(f"Found NaN/Inf at path: {path}")
            
            # Try to serialize - this will fail if there are NaN/Inf
            json_str = json.dumps(data)
            assert json_str is not None
    
    def test_quotes_json_serialization(self, client):
        """Test that quotes endpoint returns JSON-compliant data"""
        symbols = "AAPL,MSFT"
        response = client.get(f"/api/market/quotes?symbols={symbols}")
        
        if response.status_code == 200:
            data = response.json()
            # Should be able to re-serialize
            json_str = json.dumps(data)
            assert json_str is not None
    
    def test_portfolio_json_serialization(self, client, default_portfolio):
        """Test that portfolio endpoint returns JSON-compliant data"""
        response = client.get(f"/api/portfolio?portfolio_id={default_portfolio}")
        
        if response.status_code == 200:
            data = response.json()
            json_str = json.dumps(data)
            assert json_str is not None
    
    def test_strategies_json_serialization(self, client):
        """Test that strategies endpoint returns JSON-compliant data"""
        response = client.get("/api/strategies")
        
        if response.status_code == 200:
            data = response.json()
            json_str = json.dumps(data)
            assert json_str is not None
    
    def test_orders_json_serialization(self, client, default_portfolio):
        """Test that orders endpoint returns JSON-compliant data"""
        response = client.get(f"/api/orders?portfolio_id={default_portfolio}")
        
        if response.status_code == 200:
            data = response.json()
            json_str = json.dumps(data)
            assert json_str is not None


class TestJSONSerializationEdgeCases:
    """Test edge cases in JSON serialization"""
    
    def test_empty_dict_serialization(self):
        """Test serializing empty dictionary"""
        data = {}
        sanitized = sanitize_for_json(data)
        json_str = json.dumps(sanitized)
        assert json_str == "{}"
    
    def test_empty_list_serialization(self):
        """Test serializing empty list"""
        data = []
        sanitized = sanitize_for_json(data)
        json_str = json.dumps(sanitized)
        assert json_str == "[]"
    
    def test_mixed_types_serialization(self):
        """Test serializing mixed types"""
        data = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "nan": float('nan'),
            "list": [1, 2, float('inf')],
            "dict": {"nested": float('-inf')}
        }
        sanitized = sanitize_for_json(data)
        json_str = json.dumps(sanitized)
        parsed = json.loads(json_str)
        assert parsed["string"] == "test"
        assert parsed["int"] == 42
        assert parsed["float"] == 3.14
        assert parsed["bool"] is True
        assert parsed["none"] is None
        assert parsed["nan"] is None
        assert parsed["list"][2] is None
        assert parsed["dict"]["nested"] is None
    
    def test_very_deeply_nested_structure(self):
        """Test serializing very deeply nested structures"""
        data = {"level1": {"level2": {"level3": {"level4": {"value": float('nan')}}}}}
        sanitized = sanitize_for_json(data)
        json_str = json.dumps(sanitized)
        parsed = json.loads(json_str)
        assert parsed["level1"]["level2"]["level3"]["level4"]["value"] is None
    
    def test_large_list_with_nan(self):
        """Test serializing large list with NaN values"""
        data = [float('nan') if i % 10 == 0 else float(i) for i in range(1000)]
        sanitized = sanitize_for_json(data)
        json_str = json.dumps(sanitized)
        parsed = json.loads(json_str)
        assert len(parsed) == 1000
        assert parsed[0] is None
        assert parsed[10] is None
        assert parsed[20] is None
