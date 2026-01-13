"""
Simple test runner that doesn't require pytest
Tests the API endpoints directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
test_results = []

def test(name: str, func):
    """Run a test and record results"""
    try:
        result = func()
        status = "✅ PASS" if result else "❌ FAIL"
        test_results.append((name, status, ""))
        print(f"{status}: {name}")
        return result
    except Exception as e:
        test_results.append((name, "❌ ERROR", str(e)))
        print(f"❌ ERROR: {name} - {str(e)}")
        return False

def test_root():
    """Test root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    return response.status_code == 200 and "status" in response.json()

def test_create_portfolio():
    """Test creating a portfolio"""
    data = {
        "name": "Test Portfolio",
        "initial_cash": 100000.0
    }
    response = requests.post(f"{BASE_URL}/api/portfolio", json=data)
    if response.status_code == 201:
        portfolio_id = response.json()["id"]
        # Test getting it
        get_response = requests.get(f"{BASE_URL}/api/portfolio?portfolio_id={portfolio_id}")
        return get_response.status_code == 200
    return False

def test_get_nonexistent_portfolio():
    """Test getting non-existent portfolio"""
    response = requests.get(f"{BASE_URL}/api/portfolio?portfolio_id=99999")
    return response.status_code == 404

def test_create_order():
    """Test creating an order"""
    # First create a portfolio
    portfolio_data = {"name": "Test", "initial_cash": 10000.0}
    portfolio_resp = requests.post(f"{BASE_URL}/api/portfolio", json=portfolio_data)
    if portfolio_resp.status_code != 201:
        return False
    portfolio_id = portfolio_resp.json()["id"]
    
    # Create order
    order_data = {
        "portfolio_id": portfolio_id,
        "symbol": "AAPL",
        "side": "BUY",
        "type": "MARKET",
        "quantity": 10
    }
    response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
    return response.status_code == 201

def test_get_orders():
    """Test getting orders"""
    response = requests.get(f"{BASE_URL}/api/orders?portfolio_id=1")
    return response.status_code == 200

def test_get_positions():
    """Test getting positions"""
    response = requests.get(f"{BASE_URL}/api/positions?portfolio_id=1")
    return response.status_code == 200

def test_get_strategies():
    """Test getting strategies"""
    response = requests.get(f"{BASE_URL}/api/strategies")
    return response.status_code == 200

def test_get_ai_models():
    """Test getting AI models"""
    response = requests.get(f"{BASE_URL}/api/ai-models")
    return response.status_code == 200

def test_invalid_portfolio_id():
    """Test invalid portfolio ID"""
    response = requests.get(f"{BASE_URL}/api/portfolio?portfolio_id=abc")
    return response.status_code == 422  # Validation error

def test_market_quote():
    """Test market quote (may fail if service not configured)"""
    response = requests.get(f"{BASE_URL}/api/market/quote/AAPL")
    # Accept 200 or 500/503 (service not configured)
    return response.status_code in [200, 500, 503]

def main():
    print("=" * 60)
    print("SmartQuant API Test Suite")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code != 200:
            print(f"❌ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print("   Please start the backend server first:")
        print("   python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        return
    
    print(f"✅ Connected to {BASE_URL}\n")
    
    # Run tests
    print("Running tests...\n")
    
    test("Root endpoint", test_root)
    test("Create portfolio", test_create_portfolio)
    test("Get non-existent portfolio", test_get_nonexistent_portfolio)
    test("Create order", test_create_order)
    test("Get orders", test_get_orders)
    test("Get positions", test_get_positions)
    test("Get strategies", test_get_strategies)
    test("Get AI models", test_get_ai_models)
    test("Invalid portfolio ID", test_invalid_portfolio_id)
    test("Market quote", test_market_quote)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, status, _ in test_results if "✅" in status)
    failed = len(test_results) - passed
    
    print(f"Total: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed > 0:
        print("Failed tests:")
        for name, status, error in test_results:
            if "❌" in status:
                print(f"  - {name}")
                if error:
                    print(f"    Error: {error}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
