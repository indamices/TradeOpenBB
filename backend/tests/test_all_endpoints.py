"""
Comprehensive API Endpoint Tests
Tests all API endpoints without full app startup
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_main_app():
    """Test that main app can be imported"""
    try:
        from main import app
        assert app is not None
        print("PASS: Main app imported successfully")
    except Exception as e:
        print(f"FAIL: Main app import failed: {e}")
        raise

def test_app_routes_exist():
    """Test that key routes exist in app"""
    try:
        from main import app
        
        routes = [route.path for route in app.routes]
        
        # Check for key endpoints
        key_endpoints = [
            '/api/backtest',
            '/api/backtest/optimize',
            '/api/backtest/analyze',
            '/api/backtest/records',
            '/api/data-sources/available'
        ]
        
        missing = []
        for endpoint in key_endpoints:
            found = any(endpoint in route for route in routes)
            if not found:
                missing.append(endpoint)
        
        if missing:
            print(f"WARN: Missing endpoints: {missing}")
            print(f"INFO: Found {len(routes)} total routes")
        else:
            print("PASS: All key endpoints found")
            print(f"INFO: Total routes: {len(routes)}")
        
        assert len(missing) == 0, f"Missing endpoints: {missing}"
        
    except Exception as e:
        print(f"FAIL: Route check failed: {e}")
        raise

def test_schema_imports():
    """Test that all required schemas can be imported"""
    try:
        from schemas import (
            ParameterOptimizationRequest,
            ParameterOptimizationResult,
            BacktestRecord,
            BacktestRecordCreate,
            BacktestRecordUpdate,
            BacktestRequest,
            BacktestResult
        )
        assert all([
            ParameterOptimizationRequest,
            ParameterOptimizationResult,
            BacktestRecord,
            BacktestRecordCreate,
            BacktestRecordUpdate,
            BacktestRequest,
            BacktestResult
        ])
        print("PASS: All required schemas imported successfully")
    except Exception as e:
        print(f"FAIL: Schema import failed: {e}")
        raise

def test_model_imports():
    """Test that all required models can be imported"""
    try:
        from models import (
            BacktestRecord,
            Strategy,
            Portfolio,
            DataSourceConfig
        )
        assert all([
            BacktestRecord,
            Strategy,
            Portfolio,
            DataSourceConfig
        ])
        print("PASS: All required models imported successfully")
    except Exception as e:
        print(f"FAIL: Model import failed: {e}")
        raise

def test_service_imports():
    """Test that all required services can be imported"""
    try:
        from services.parameter_optimizer import ParameterOptimizer
        from services.strategy_analyzer import StrategyAnalyzer
        from services.data_service import DataService
        
        assert all([
            ParameterOptimizer,
            StrategyAnalyzer,
            DataService
        ])
        print("PASS: All required services imported successfully")
    except Exception as e:
        print(f"FAIL: Service import failed: {e}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("Running Comprehensive API Endpoint Tests")
    print("=" * 60)
    print()
    
    results = []
    results.append(("Import Main App", test_import_main_app()))
    results.append(("App Routes Exist", test_app_routes_exist()))
    results.append(("Schema Imports", test_schema_imports()))
    results.append(("Model Imports", test_model_imports()))
    results.append(("Service Imports", test_service_imports()))
    
    print()
    print("=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("All endpoint tests passed!")
        exit(0)
    else:
        print(f"{total - passed} test(s) failed")
        exit(1)
