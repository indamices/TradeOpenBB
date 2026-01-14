#!/usr/bin/env python3
"""
Simple verification script for new API features
This script verifies the schema and code changes without requiring pytest
"""
import sys
import os
import ast

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def verify_schemas():
    """Verify schema changes"""
    print("Verifying schema changes...")
    schemas_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'schemas.py')
    
    try:
        with open(schemas_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check BacktestResult has time series fields
        checks = [
            ('equity_curve: Optional', 'BacktestResult equity_curve field'),
            ('drawdown_series: Optional', 'BacktestResult drawdown_series field'),
            ('trades: Optional', 'BacktestResult trades field'),
            ('ChatRequest', 'ChatRequest class'),
            ('ChatResponse', 'ChatResponse class'),
            ('conversation_id: Optional', 'ChatRequest conversation_id field'),
            ('message: str', 'ChatRequest message field'),
        ]
        
        all_found = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ Found: {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ✗ Schema verification failed: {e}")
        return False

def verify_api_endpoints():
    """Verify API endpoints exist in main.py"""
    print("\nVerifying API endpoints...")
    main_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'main.py')
    
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        endpoints_to_check = [
            ('/api/market/quotes', 'GET /api/market/quotes'),
            ('/api/market/indicators/', 'GET /api/market/indicators/{symbol}'),
            ('/api/market/overview', 'GET /api/market/overview'),
            ('/api/ai/chat', 'POST /api/ai/chat'),
            ('/api/ai/chat/', 'GET /api/ai/chat/{conversation_id}'),
            ('/api/ai/suggestions', 'POST /api/ai/suggestions'),
        ]
        
        all_found = True
        for pattern, description in endpoints_to_check:
            if pattern in content:
                print(f"  ✓ Found: {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ✗ Endpoint verification failed: {e}")
        return False

def verify_backtest_engine():
    """Verify backtest engine returns time series data"""
    print("\nVerifying backtest engine changes...")
    backtest_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'backtest_engine.py')
    
    try:
        with open(backtest_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for time series data handling
        checks = [
            ('equity_curve_with_dates', 'Equity curve with dates tracking'),
            ('drawdown_series', 'Drawdown series calculation'),
            ('trades_data', 'Trades data formatting'),
        ]
        
        all_found = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ Found: {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ✗ Backtest engine verification failed: {e}")
        return False

def verify_types():
    """Verify TypeScript type definitions"""
    print("\nVerifying TypeScript types...")
    types_ts_path = os.path.join(os.path.dirname(__file__), 'types.ts')
    
    try:
        with open(types_ts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('equity_curve?:', 'BacktestResult equity_curve'),
            ('drawdown_series?:', 'BacktestResult drawdown_series'),
            ('trades?:', 'BacktestResult trades'),
            ('interface ChatMessage', 'ChatMessage interface'),
            ('interface ChatRequest', 'ChatRequest interface'),
            ('interface ChatResponse', 'ChatResponse interface'),
        ]
        
        all_found = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✓ Found: {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ✗ TypeScript types verification failed: {e}")
        return False

def verify_navigation():
    """Verify navigation changes"""
    print("\nVerifying navigation changes...")
    
    app_tsx_path = os.path.join(os.path.dirname(__file__), 'App.tsx')
    layout_tsx_path = os.path.join(os.path.dirname(__file__), 'components', 'Layout.tsx')
    
    try:
        # Check App.tsx
        with open(app_tsx_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check Layout.tsx
        with open(layout_tsx_path, 'r', encoding='utf-8') as f:
            layout_content = f.read()
        
        checks = [
            ('backtest', 'Backtest route in App.tsx'),
            ('ai-chat', 'AI chat route in App.tsx'),
            ("'backtest'", 'Backtest menu item in Layout.tsx'),
            ("'ai-chat'", 'AI chat menu item in Layout.tsx'),
        ]
        
        all_found = True
        for pattern, description in checks:
            content_to_check = app_content if 'App.tsx' in description else layout_content
            if pattern in content_to_check:
                print(f"  ✓ Found: {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_found = False
        
        # Check that 'trade' is removed
        if "'trade'" not in app_content:
            print("  ✓ Trade panel removed from App.tsx")
        else:
            print("  ✗ Trade panel still in App.tsx")
            all_found = False
        
        if "'trade'" not in layout_content:
            print("  ✓ Trade menu item removed from Layout.tsx")
        else:
            print("  ✗ Trade menu item still in Layout.tsx")
            all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ✗ Navigation verification failed: {e}")
        return False

def main():
    """Run all verifications"""
    print("="*60)
    print("Verifying New API Features")
    print("="*60)
    
    results = []
    
    results.append(("Schemas", verify_schemas()))
    results.append(("API Endpoints", verify_api_endpoints()))
    results.append(("Backtest Engine", verify_backtest_engine()))
    results.append(("TypeScript Types", verify_types()))
    results.append(("Navigation", verify_navigation()))
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
