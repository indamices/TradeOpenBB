"""
Run integration tests
"""
import sys
import os
import subprocess

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# Test files to run
test_files = [
    'tests/test_integration_data_service.py',
    'tests/test_integration_backtest.py',
    'tests/test_api_endpoints.py'
]

print("=" * 60)
print("Running Integration Tests")
print("=" * 60)
print()

exit_codes = []

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
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {test_file} took longer than 5 minutes")
        exit_codes.append((test_file, -1))
    except Exception as e:
        print(f"ERROR running {test_file}: {e}")
        exit_codes.append((test_file, -2))

print("\n" + "=" * 60)
print("Integration Test Summary")
print("=" * 60)

for test_file, exit_code in exit_codes:
    status = "PASS" if exit_code == 0 else "FAIL"
    print(f"{status}: {test_file}")

total_tests = len(exit_codes)
passed_tests = sum(1 for _, code in exit_codes if code == 0)

print("=" * 60)
print(f"Total: {passed_tests}/{total_tests} test suites passed")
print("=" * 60)

if passed_tests == total_tests:
    print("All integration tests passed!")
    sys.exit(0)
else:
    print(f"{total_tests - passed_tests} test suite(s) failed")
    sys.exit(1)
