"""
Test runner script
Run all tests with pytest
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Run all tests"""
    # Test files to run
    test_files = [
        'tests/test_parameter_optimizer.py',
        'tests/test_strategy_analyzer.py',
        'tests/test_futu_service.py',
        'tests/test_backtest_records.py'
    ]
    
    # Run tests
    exit_code = pytest.main([
        *test_files,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-x',  # Stop on first failure (optional)
        # '--cov=services',  # Coverage report (if pytest-cov installed)
        # '--cov-report=html',  # HTML coverage report
    ])
    
    return exit_code

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
