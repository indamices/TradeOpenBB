#!/usr/bin/env python3
"""
Run tests for new API endpoints
"""
import sys
import os
import subprocess

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_tests():
    """Run new API tests"""
    test_files = [
        'backend/tests/test_backtest_timeseries.py',
        'backend/tests/test_api_market_extended.py',
        'backend/tests/test_api_ai_chat.py'
    ]
    
    results = []
    
    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"Running tests in {test_file}")
        print('='*60)
        
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', test_file, '-v', '--tb=short'],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            results.append({
                'file': test_file,
                'success': result.returncode == 0,
                'returncode': result.returncode
            })
        except Exception as e:
            print(f"Error running {test_file}: {e}")
            results.append({
                'file': test_file,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    for result in results:
        status = "✓ PASSED" if result['success'] else "✗ FAILED"
        print(f"{status}: {result['file']}")
        if not result['success']:
            if 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Return code: {result['returncode']}")
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
