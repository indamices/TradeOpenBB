"""
AI Strategy Analyzer service
Analyzes backtest results and provides optimization suggestions using AI
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

try:
    from ..ai_service_factory import get_default_model, create_provider
    from ..schemas import BacktestResult
except ImportError:
    from ai_service_factory import get_default_model, create_provider
    from schemas import BacktestResult

logger = logging.getLogger(__name__)


class StrategyAnalyzer:
    """Service for analyzing backtest results and providing AI-powered suggestions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_backtest_result(
        self,
        backtest_result: Dict[str, Any],
        strategy_code: str,
        strategy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze backtest result and provide AI-powered suggestions
        
        Args:
            backtest_result: BacktestResult dictionary
            strategy_code: Strategy code
            strategy_name: Strategy name (optional)
        
        Returns:
            Analysis result with suggestions and recommendations
        """
        try:
            # Get AI model
            model_config = get_default_model(self.db)
            if not model_config:
                raise ValueError("No AI model configured")
            
            # Create provider
            provider = create_provider(model_config)
            
            # Prepare analysis prompt
            prompt = self._create_analysis_prompt(backtest_result, strategy_code, strategy_name)
            
            # Get AI analysis using chat method
            response = await provider.chat(prompt, conversation_history=None)
            
            # Parse response (assuming it's a JSON or structured text)
            analysis = self._parse_ai_response(response)
            
            # Add structured analysis
            structured_analysis = self._create_structured_analysis(backtest_result)
            
            return {
                'ai_analysis': analysis,
                'structured_analysis': structured_analysis,
                'recommendations': analysis.get('recommendations', []),
                'strengths': analysis.get('strengths', []),
                'weaknesses': analysis.get('weaknesses', []),
                'suggestions': analysis.get('suggestions', [])
            }
            
        except Exception as e:
            logger.error(f"Strategy analysis failed: {str(e)}")
            # Return basic analysis even if AI fails
            return {
                'error': str(e),
                'structured_analysis': self._create_structured_analysis(backtest_result),
                'recommendations': [],
                'strengths': [],
                'weaknesses': [],
                'suggestions': []
            }
    
    def _create_analysis_prompt(
        self,
        backtest_result: Dict[str, Any],
        strategy_code: str,
        strategy_name: Optional[str]
    ) -> str:
        """Create prompt for AI analysis"""
        
        # Extract key metrics
        metrics = {
            'sharpe_ratio': backtest_result.get('sharpe_ratio', 0),
            'sortino_ratio': backtest_result.get('sortino_ratio', 0),
            'annualized_return': backtest_result.get('annualized_return', 0),
            'max_drawdown': backtest_result.get('max_drawdown', 0),
            'win_rate': backtest_result.get('win_rate', 0),
            'total_trades': backtest_result.get('total_trades', 0),
            'total_return': backtest_result.get('total_return', 0)
        }
        
        prompt = f"""请分析以下交易策略的回测结果，并提供专业的优化建议。

策略名称: {strategy_name or '未命名策略'}

回测指标:
- 夏普比率 (Sharpe Ratio): {metrics['sharpe_ratio']:.4f}
- 索提诺比率 (Sortino Ratio): {metrics.get('sortino_ratio', 'N/A')}
- 年化收益率: {metrics['annualized_return']:.2f}%
- 最大回撤: {metrics['max_drawdown']:.2f}%
- 胜率: {metrics.get('win_rate', 'N/A')}%
- 总交易次数: {metrics['total_trades']}
- 总收益率: {metrics['total_return']:.2f}%

策略代码:
```python
{strategy_code[:2000]}  # Limit to first 2000 chars
```

请提供以下分析：
1. 策略的优势和亮点
2. 策略存在的问题和风险
3. 具体的优化建议（包括参数调整、规则改进等）
4. 风险评估和注意事项

请以JSON格式返回，格式如下：
{{
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["问题1", "问题2"],
    "recommendations": ["建议1", "建议2"],
    "suggestions": ["优化建议1", "优化建议2"],
    "risk_assessment": "风险评估文本"
}}
"""
        return prompt
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        import json
        import re
        
        # Try to extract JSON from response
        try:
            # Look for JSON block
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
        
        # Fallback: Parse as text
        return {
            'raw_response': response,
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'suggestions': []
        }
    
    def _create_structured_analysis(self, backtest_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured analysis based on metrics"""
        
        metrics = {
            'sharpe_ratio': backtest_result.get('sharpe_ratio', 0),
            'sortino_ratio': backtest_result.get('sortino_ratio', 0),
            'annualized_return': backtest_result.get('annualized_return', 0),
            'max_drawdown': backtest_result.get('max_drawdown', 0),
            'win_rate': backtest_result.get('win_rate', 0),
            'total_trades': backtest_result.get('total_trades', 0),
            'total_return': backtest_result.get('total_return', 0)
        }
        
        # Evaluate metrics
        evaluation = {
            'sharpe_ratio': {
                'value': metrics['sharpe_ratio'],
                'rating': self._rate_sharpe(metrics['sharpe_ratio']),
                'comment': self._comment_sharpe(metrics['sharpe_ratio'])
            },
            'return': {
                'value': metrics['annualized_return'],
                'rating': self._rate_return(metrics['annualized_return']),
                'comment': self._comment_return(metrics['annualized_return'])
            },
            'drawdown': {
                'value': abs(metrics['max_drawdown']),
                'rating': self._rate_drawdown(abs(metrics['max_drawdown'])),
                'comment': self._comment_drawdown(abs(metrics['max_drawdown']))
            },
            'win_rate': {
                'value': metrics.get('win_rate', 0),
                'rating': self._rate_win_rate(metrics.get('win_rate', 0)),
                'comment': self._comment_win_rate(metrics.get('win_rate', 0))
            },
            'trades': {
                'value': metrics['total_trades'],
                'rating': self._rate_trades(metrics['total_trades']),
                'comment': self._comment_trades(metrics['total_trades'])
            }
        }
        
        return {
            'metrics': metrics,
            'evaluation': evaluation,
            'overall_rating': self._calculate_overall_rating(evaluation)
        }
    
    def _rate_sharpe(self, sharpe: float) -> str:
        """Rate Sharpe ratio"""
        if sharpe >= 2.0:
            return 'excellent'
        elif sharpe >= 1.5:
            return 'good'
        elif sharpe >= 1.0:
            return 'fair'
        elif sharpe >= 0.5:
            return 'poor'
        else:
            return 'very_poor'
    
    def _comment_sharpe(self, sharpe: float) -> str:
        """Comment on Sharpe ratio"""
        if sharpe >= 2.0:
            return '优秀的风险调整收益，策略表现优异'
        elif sharpe >= 1.5:
            return '良好的风险调整收益'
        elif sharpe >= 1.0:
            return '风险调整收益一般，有改进空间'
        elif sharpe >= 0.5:
            return '风险调整收益较差，需要优化'
        else:
            return '风险调整收益很差，策略需要重大改进'
    
    def _rate_return(self, annual_return: float) -> str:
        """Rate annualized return"""
        if annual_return >= 20:
            return 'excellent'
        elif annual_return >= 10:
            return 'good'
        elif annual_return >= 5:
            return 'fair'
        elif annual_return >= 0:
            return 'poor'
        else:
            return 'very_poor'
    
    def _comment_return(self, annual_return: float) -> str:
        """Comment on annualized return"""
        if annual_return >= 20:
            return '年化收益率很高，表现优秀'
        elif annual_return >= 10:
            return '年化收益率较好'
        elif annual_return >= 5:
            return '年化收益率一般'
        elif annual_return >= 0:
            return '年化收益率偏低'
        else:
            return '年化收益率为负，策略亏损'
    
    def _rate_drawdown(self, drawdown: float) -> str:
        """Rate max drawdown"""
        if drawdown <= 10:
            return 'excellent'
        elif drawdown <= 20:
            return 'good'
        elif drawdown <= 30:
            return 'fair'
        elif drawdown <= 50:
            return 'poor'
        else:
            return 'very_poor'
    
    def _comment_drawdown(self, drawdown: float) -> str:
        """Comment on max drawdown"""
        if drawdown <= 10:
            return '最大回撤很小，风险控制很好'
        elif drawdown <= 20:
            return '最大回撤在可接受范围内'
        elif drawdown <= 30:
            return '最大回撤较大，需要注意风险'
        elif drawdown <= 50:
            return '最大回撤很大，风险较高'
        else:
            return '最大回撤非常大，存在重大风险'
    
    def _rate_win_rate(self, win_rate: Optional[float]) -> str:
        """Rate win rate"""
        if win_rate is None:
            return 'unknown'
        if win_rate >= 60:
            return 'excellent'
        elif win_rate >= 50:
            return 'good'
        elif win_rate >= 40:
            return 'fair'
        else:
            return 'poor'
    
    def _comment_win_rate(self, win_rate: Optional[float]) -> str:
        """Comment on win rate"""
        if win_rate is None:
            return '无法计算胜率'
        if win_rate >= 60:
            return f'胜率很高({win_rate:.1f}%)，交易质量好'
        elif win_rate >= 50:
            return f'胜率较好({win_rate:.1f}%)'
        elif win_rate >= 40:
            return f'胜率一般({win_rate:.1f}%)，需要提高'
        else:
            return f'胜率较低({win_rate:.1f}%)，需要优化策略'
    
    def _rate_trades(self, total_trades: int) -> str:
        """Rate total trades"""
        if total_trades >= 100:
            return 'high'
        elif total_trades >= 50:
            return 'medium'
        elif total_trades >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def _comment_trades(self, total_trades: int) -> str:
        """Comment on total trades"""
        if total_trades >= 100:
            return f'交易次数很多({total_trades})，策略较为活跃'
        elif total_trades >= 50:
            return f'交易次数适中({total_trades})'
        elif total_trades >= 20:
            return f'交易次数较少({total_trades})，可能错过机会'
        else:
            return f'交易次数很少({total_trades})，策略可能过于保守'
    
    def _calculate_overall_rating(self, evaluation: Dict[str, Any]) -> str:
        """Calculate overall rating"""
        ratings = {
            'excellent': 5,
            'good': 4,
            'fair': 3,
            'poor': 2,
            'very_poor': 1,
            'unknown': 0
        }
        
        scores = []
        for key, value in evaluation.items():
            if isinstance(value, dict) and 'rating' in value:
                rating = value['rating']
                scores.append(ratings.get(rating, 0))
        
        if not scores:
            return 'unknown'
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 4.5:
            return 'excellent'
        elif avg_score >= 3.5:
            return 'good'
        elif avg_score >= 2.5:
            return 'fair'
        elif avg_score >= 1.5:
            return 'poor'
        else:
            return 'very_poor'
