"""
Simple standalone tests that don't require full application setup
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_parameter_optimizer():
    """Test that parameter optimizer can be imported"""
    try:
        from services.parameter_optimizer import ParameterOptimizer
        assert ParameterOptimizer is not None
        print("PASS: ParameterOptimizer import successful")
        return True
    except Exception as e:
        print(f"FAIL: ParameterOptimizer import failed: {e}")
        return False

def test_import_strategy_analyzer():
    """Test that strategy analyzer can be imported"""
    try:
        from services.strategy_analyzer import StrategyAnalyzer
        assert StrategyAnalyzer is not None
        print("PASS: StrategyAnalyzer import successful")
        return True
    except Exception as e:
        print(f"FAIL: StrategyAnalyzer import failed: {e}")
        return False

def test_import_futu_service():
    """Test that futu service can be imported"""
    try:
        from futu_service import FutuService
        assert FutuService is not None
        print("PASS: FutuService import successful")
        return True
    except Exception as e:
        print(f"FAIL: FutuService import failed: {e}")
        return False

def test_import_schemas():
    """Test that schemas can be imported"""
    try:
        from schemas import (
            ParameterOptimizationRequest,
            ParameterOptimizationResult,
            BacktestRecord,
            BacktestRecordCreate
        )
        assert ParameterOptimizationRequest is not None
        assert ParameterOptimizationResult is not None
        print("PASS: Schemas import successful")
        return True
    except Exception as e:
        print(f"FAIL: Schemas import failed: {e}")
        return False

def test_parameter_extraction():
    """Test parameter extraction functionality"""
    try:
        from services.parameter_optimizer import ParameterOptimizer
        from unittest.mock import Mock
        
        optimizer = ParameterOptimizer(Mock())
        code = """
short_sma = 20
long_sma = 50
"""
        params = optimizer.extract_parameters_from_code(code)
        assert isinstance(params, dict)
        print(f"PASS: Parameter extraction successful, found params: {list(params.keys())}")
        return True
    except Exception as e:
        print(f"FAIL: Parameter extraction failed: {e}")
        return False

def test_parameter_replacement():
    """Test parameter replacement functionality"""
    try:
        from services.parameter_optimizer import ParameterOptimizer
        from unittest.mock import Mock
        
        optimizer = ParameterOptimizer(Mock())
        code = "short_sma = 20\nlong_sma = 50"
        params = {'short_sma': 30, 'long_sma': 60}
        modified = optimizer.replace_parameters_in_code(code, params)
        assert 'short_sma = 30' in modified
        assert 'long_sma = 60' in modified
        print("PASS: Parameter replacement successful")
        return True
    except Exception as e:
        print(f"FAIL: Parameter replacement failed: {e}")
        return False

if __name__ == '__main__':
    print("Running simple import and functionality tests...\n")
    
    results = []
    results.append(("Import ParameterOptimizer", test_import_parameter_optimizer()))
    results.append(("Import StrategyAnalyzer", test_import_strategy_analyzer()))
    results.append(("Import FutuService", test_import_futu_service()))
    results.append(("Import Schemas", test_import_schemas()))
    results.append(("Parameter Extraction", test_parameter_extraction()))
    results.append(("Parameter Replacement", test_parameter_replacement()))
    
    print("\n" + "="*50)
    print("Test Results Summary:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print("="*50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
        exit(0)
    else:
        print(f"{total - passed} test(s) failed")
        exit(1)
