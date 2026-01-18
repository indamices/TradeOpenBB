"""
Parameter optimization service for trading strategies
Implements grid search algorithm to find optimal parameters
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from itertools import product
import logging
import asyncio
from sqlalchemy.orm import Session

try:
    from ..backtest_engine import run_backtest
    from ..schemas import BacktestRequest, BacktestResult
    from ..models import Strategy
except ImportError:
    from backtest_engine import run_backtest
    from schemas import BacktestRequest, BacktestResult
    from models import Strategy

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """Service for optimizing strategy parameters using grid search"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_parameters_from_code(self, strategy_code: str) -> Dict[str, List]:
        """
        Extract parameter names and their possible values from strategy code
        
        This is a simple heuristic-based extraction. For better results,
        parameters should be explicitly defined in a structured format.
        
        Args:
            strategy_code: Strategy code string
        
        Returns:
            Dict mapping parameter names to lists of possible values
        """
        parameters = {}
        
        # Common parameter patterns in strategy code
        # Look for common patterns like SMA periods, RSI thresholds, etc.
        
        # Example: short_sma = 20, long_sma = 50
        import re
        
        # Find variable assignments that look like parameters
        # Pattern: variable_name = number
        param_pattern = r'(\w+)\s*=\s*(\d+\.?\d*)'
        matches = re.findall(param_pattern, strategy_code)
        
        for var_name, value in matches:
            try:
                num_value = float(value)
                # If it's a reasonable parameter value (not too large), consider it a parameter
                if 0 < num_value <= 1000:
                    if var_name not in parameters:
                        # Generate a range around the current value
                        base_value = int(num_value)
                        if base_value <= 5:
                            parameters[var_name] = list(range(1, base_value + 3))
                        elif base_value <= 20:
                            parameters[var_name] = list(range(max(1, base_value - 5), base_value + 6, 1))
                        elif base_value <= 50:
                            parameters[var_name] = list(range(max(1, base_value - 10), base_value + 11, 5))
                        else:
                            parameters[var_name] = list(range(max(1, base_value - 20), base_value + 21, 10))
            except ValueError:
                continue
        
        return parameters
    
    def replace_parameters_in_code(self, strategy_code: str, params: Dict[str, Any]) -> str:
        """
        Replace parameter values in strategy code
        
        Args:
            strategy_code: Original strategy code
            params: Dict mapping parameter names to values
        
        Returns:
            Modified strategy code with new parameter values
        """
        modified_code = strategy_code
        
        for param_name, param_value in params.items():
            # Replace parameter assignments
            # Pattern: param_name = value
            import re
            pattern = rf'(\b{re.escape(param_name)}\s*=\s*)(\d+\.?\d*)'
            replacement = rf'\g<1>{param_value}'
            modified_code = re.sub(pattern, replacement, modified_code)
        
        return modified_code
    
    def generate_parameter_combinations(self, parameter_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Generate all parameter combinations for grid search
        
        Args:
            parameter_ranges: Dict mapping parameter names to lists of possible values
        
        Returns:
            List of parameter dictionaries (all combinations)
        """
        if not parameter_ranges:
            return [{}]
        
        param_names = list(parameter_ranges.keys())
        param_values = [parameter_ranges[name] for name in param_names]
        
        # Generate all combinations
        combinations = []
        for combo in product(*param_values):
            param_dict = {param_names[i]: combo[i] for i in range(len(param_names))}
            combinations.append(param_dict)
        
        return combinations
    
    async def optimize_parameters(
        self,
        strategy_id: int,
        optimization_request: 'ParameterOptimizationRequest',
        optimization_metric: str = 'sharpe_ratio'
    ) -> 'ParameterOptimizationResult':
        """
        Optimize strategy parameters using grid search
        
        Args:
            strategy_id: Strategy ID to optimize
            optimization_request: Optimization request with parameter ranges
            optimization_metric: Metric to optimize (default: 'sharpe_ratio')
        
        Returns:
            Optimization result with best parameters and all tested combinations
        """
        try:
            # Get strategy
            strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Get parameter ranges from request or extract from code
            if optimization_request.parameter_ranges:
                parameter_ranges = optimization_request.parameter_ranges
            else:
                # Try to extract parameters from code
                parameter_ranges = self.extract_parameters_from_code(strategy.logic_code)
                if not parameter_ranges:
                    raise ValueError("No parameters found to optimize. Please specify parameter_ranges.")
            
            # Generate all parameter combinations
            param_combinations = self.generate_parameter_combinations(parameter_ranges)
            
            logger.info(f"Testing {len(param_combinations)} parameter combinations...")
            
            # Run backtests for each combination
            results = []
            
            for i, params in enumerate(param_combinations):
                try:
                    # Replace parameters in strategy code
                    modified_code = self.replace_parameters_in_code(strategy.logic_code, params)
                    
                    # Create backtest request
                    backtest_request = BacktestRequest(
                        strategy_id=strategy_id,
                        start_date=optimization_request.start_date,
                        end_date=optimization_request.end_date,
                        initial_cash=optimization_request.initial_cash,
                        symbols=optimization_request.symbols
                    )
                    
                    # Create a modified strategy object with the new code
                    # We pass this directly to run_backtest to avoid querying from DB
                    modified_strategy = Strategy(
                        id=strategy.id,
                        name=strategy.name,
                        logic_code=modified_code,
                        target_portfolio_id=strategy.target_portfolio_id,
                        description=strategy.description,
                        is_active=strategy.is_active,
                        created_at=strategy.created_at,
                        updated_at=strategy.updated_at
                    )
                    
                    # Run backtest with modified strategy
                    # Pass the modified strategy object directly to avoid database query
                    backtest_result = await run_backtest(backtest_request, self.db, strategy=modified_strategy)
                    
                    # Extract metric value
                    metric_value = getattr(backtest_result, optimization_metric, None)
                    if metric_value is None:
                        # Try to get from dict if it's a BaseModel
                        metric_dict = backtest_result.model_dump() if hasattr(backtest_result, 'model_dump') else backtest_result.__dict__
                        metric_value = metric_dict.get(optimization_metric, 0)
                    
                    # Store result
                    results.append({
                        'parameters': params,
                        'metric_value': float(metric_value) if metric_value is not None else 0,
                        'result': backtest_result.model_dump() if hasattr(backtest_result, 'model_dump') else backtest_result.__dict__
                    })
                    
                    logger.info(f"Completed {i+1}/{len(param_combinations)}: {params} -> {optimization_metric}={metric_value:.4f}")
                    
                except Exception as e:
                    logger.warning(f"Failed to test parameters {params}: {str(e)}")
                    results.append({
                        'parameters': params,
                        'metric_value': float('-inf'),
                        'error': str(e)
                    })
            
            # Find best parameters
            valid_results = [r for r in results if 'error' not in r]
            if not valid_results:
                raise ValueError("No valid backtest results obtained")
            
            # Sort by metric value (higher is better for most metrics)
            if optimization_metric in ['sharpe_ratio', 'sortino_ratio', 'annualized_return', 'total_return', 'win_rate']:
                best_result = max(valid_results, key=lambda x: x['metric_value'])
            else:
                # For metrics like max_drawdown, lower is better
                best_result = min(valid_results, key=lambda x: x['metric_value'])
            
            # Return optimization result
            return {
                'best_parameters': best_result['parameters'],
                'best_metric_value': best_result['metric_value'],
                'best_result': best_result['result'],
                'all_results': results,
                'total_combinations': len(param_combinations),
                'valid_combinations': len(valid_results),
                'optimization_metric': optimization_metric
            }
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {str(e)}")
            raise


# Request/Response schemas (will be defined in schemas.py)
# These are placeholder classes for type hints
class ParameterOptimizationRequest:
    def __init__(self, **kwargs):
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.initial_cash = kwargs.get('initial_cash', 100000)
        self.symbols = kwargs.get('symbols', [])
        self.parameter_ranges = kwargs.get('parameter_ranges', {})

class ParameterOptimizationResult:
    def __init__(self, **kwargs):
        self.best_parameters = kwargs.get('best_parameters', {})
        self.best_metric_value = kwargs.get('best_metric_value', 0)
        self.best_result = kwargs.get('best_result', {})
        self.all_results = kwargs.get('all_results', [])
        self.total_combinations = kwargs.get('total_combinations', 0)
        self.valid_combinations = kwargs.get('valid_combinations', 0)
        self.optimization_metric = kwargs.get('optimization_metric', 'sharpe_ratio')
