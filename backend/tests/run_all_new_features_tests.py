"""
Run all tests for new features
Comprehensive test suite for parameter optimization, AI analysis, and backtest records
"""
import sys
import os
import subprocess
from datetime import datetime

# Change to backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(backend_dir)

# Test files to run
test_files = [
    # New API tests
    'tests/test_api_parameter_optimization.py',
    'tests/test_api_ai_analysis.py',
    'tests/test_api_backtest_records_integration.py',
    
    # Service method tests
    'tests/test_trading_service_methods.py',
    
    # Integration tests
    'tests/test_new_features_integration.py',
    
    # Unit tests (related to new features)
    'tests/test_parameter_optimizer.py',
    'tests/test_strategy_analyzer.py',
    'tests/test_backtest_records.py',
]

print("=" * 70)
print("运行新增功能完整测试套件")
print("=" * 70)
print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

results = []
total_passed = 0
total_failed = 0
total_skipped = 0

for test_file in test_files:
    print(f"\n{'=' * 70}")
    print(f"运行: {test_file}")
    print('=' * 70)
    
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', test_file, '-v', '--tb=short', '--ignore=conftest.py'],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=backend_dir
        )
        
        # Print output
        if result.stdout:
            # Extract summary
            lines = result.stdout.split('\n')
            for line in lines:
                if 'passed' in line.lower() or 'failed' in line.lower() or 'skipped' in line.lower():
                    print(line)
                    # Parse results
                    if 'passed' in line.lower():
                        try:
                            passed_count = int(line.split()[0])
                            total_passed += passed_count
                        except:
                            pass
                    if 'failed' in line.lower():
                        try:
                            failed_count = int(line.split()[0])
                            total_failed += failed_count
                        except:
                            pass
                    if 'skipped' in line.lower():
                        try:
                            skipped_count = int(line.split()[0])
                            total_skipped += skipped_count
                        except:
                            pass
        
        results.append({
            'file': test_file,
            'exit_code': result.returncode,
            'passed': result.returncode == 0 or 'passed' in result.stdout.lower()
        })
        
        if result.returncode == 0:
            print(f"✅ PASS: {test_file}")
        else:
            print(f"⚠️  FAIL/SKIP: {test_file} (exit code: {result.returncode})")
        
    except subprocess.TimeoutExpired:
        print(f"⏱️  TIMEOUT: {test_file} 超过5分钟")
        results.append({
            'file': test_file,
            'exit_code': -1,
            'passed': False
        })
        total_failed += 1
    except Exception as e:
        print(f"❌ ERROR: {test_file} - {e}")
        results.append({
            'file': test_file,
            'exit_code': -2,
            'passed': False
        })
        total_failed += 1

print("\n" + "=" * 70)
print("测试结果总结")
print("=" * 70)

for result in results:
    status = "✅ PASS" if result['passed'] else "⚠️  FAIL/SKIP"
    print(f"{status}: {result['file']}")

print("=" * 70)
print(f"总计:")
print(f"  ✅ 通过: {total_passed}")
print(f"  ⚠️  跳过: {total_skipped}")
print(f"  ❌ 失败: {total_failed}")
print(f"  📊 总计: {len(results)} 个测试文件")
print("=" * 70)

if total_failed == 0 and total_passed > 0:
    print("\n🎉 所有测试通过！新增功能验证成功！")
    sys.exit(0)
elif total_passed > 0:
    print(f"\n⚠️  部分测试通过 ({total_passed} 通过, {total_failed} 失败/跳过)")
    sys.exit(1)
else:
    print("\n❌ 没有测试通过")
    sys.exit(1)
