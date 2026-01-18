"""
Run tests for new features
"""
import sys
import os
import subprocess

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# Test files to run
test_files = [
    'test_api_parameter_optimization.py',
    'test_api_ai_analysis.py',
    'test_api_backtest_records_integration.py',
    'test_trading_service_methods.py',
    'test_new_features_integration.py'
]

print("=" * 60)
print("Running New Features Tests")
print("=" * 60)
print()

exit_codes = []
results = []

for test_file in test_files:
    print(f"\n{'=' * 60}")
    print(f"Running: {test_file}")
    print('=' * 60)
    
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', test_file, '-v', '--tb=short', '--ignore=conftest.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        exit_codes.append((test_file, result.returncode))
        
        # Parse results
        if "passed" in result.stdout or "PASSED" in result.stdout:
            passed = True
        elif "failed" in result.stdout or "FAILED" in result.stdout:
            passed = False
        else:
            passed = result.returncode == 0
        
        results.append((test_file, passed, result.returncode))
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {test_file} took longer than 5 minutes")
        exit_codes.append((test_file, -1))
        results.append((test_file, False, -1))
    except Exception as e:
        print(f"ERROR running {test_file}: {e}")
        exit_codes.append((test_file, -2))
        results.append((test_file, False, -2))

print("\n" + "=" * 60)
print("New Features Test Summary")
print("=" * 60)

for test_file, passed, exit_code in results:
    status = "PASS" if passed else "FAIL"
    print(f"{status}: {test_file} (exit code: {exit_code})")

total_tests = len(results)
passed_tests = sum(1 for _, passed, _ in results if passed)

print("=" * 60)
print(f"Total: {passed_tests}/{total_tests} test suites passed")
print("=" * 60)

if passed_tests == total_tests:
    print("All new features tests passed!")
    sys.exit(0)
else:
    print(f"{total_tests - passed_tests} test suite(s) failed or skipped")
    sys.exit(1)
