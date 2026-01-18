"""
Unit tests for strategy analyzer
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.strategy_analyzer import StrategyAnalyzer
from schemas import BacktestResult


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_backtest_result():
    """Create a sample backtest result"""
    return {
        'sharpe_ratio': 1.8,
        'sortino_ratio': 2.1,
        'annualized_return': 15.5,
        'max_drawdown': -12.3,
        'win_rate': 55.5,
        'total_trades': 120,
        'total_return': 15.5
    }


@pytest.fixture
def analyzer(mock_db):
    """Create strategy analyzer instance"""
    return StrategyAnalyzer(mock_db)


class TestStructuredAnalysis:
    """Test structured analysis functionality"""
    
    def test_rate_sharpe_excellent(self, analyzer):
        """Test rating excellent Sharpe ratio"""
        rating = analyzer._rate_sharpe(2.5)
        assert rating == 'excellent'
    
    def test_rate_sharpe_good(self, analyzer):
        """Test rating good Sharpe ratio"""
        rating = analyzer._rate_sharpe(1.7)
        assert rating == 'good'
    
    def test_rate_sharpe_poor(self, analyzer):
        """Test rating poor Sharpe ratio"""
        rating = analyzer._rate_sharpe(0.3)
        assert rating == 'very_poor'  # Fixed: 0.3 < 0.5 should be 'very_poor'
    
    def test_rate_return_excellent(self, analyzer):
        """Test rating excellent return"""
        rating = analyzer._rate_return(25.0)
        assert rating == 'excellent'
    
    def test_rate_drawdown_excellent(self, analyzer):
        """Test rating excellent drawdown"""
        rating = analyzer._rate_drawdown(8.0)
        assert rating == 'excellent'
    
    def test_rate_drawdown_very_poor(self, analyzer):
        """Test rating very poor drawdown"""
        rating = analyzer._rate_drawdown(60.0)
        assert rating == 'very_poor'
    
    def test_rate_win_rate_excellent(self, analyzer):
        """Test rating excellent win rate"""
        rating = analyzer._rate_win_rate(65.0)
        assert rating == 'excellent'
    
    def test_create_structured_analysis(self, analyzer, sample_backtest_result):
        """Test creating structured analysis"""
        analysis = analyzer._create_structured_analysis(sample_backtest_result)
        
        assert 'metrics' in analysis
        assert 'evaluation' in analysis
        assert 'overall_rating' in analysis
        
        assert analysis['metrics']['sharpe_ratio'] == 1.8
        assert analysis['evaluation']['sharpe_ratio']['rating'] == 'good'
        assert analysis['overall_rating'] in ['excellent', 'good', 'fair', 'poor', 'very_poor']


class TestAIAnalysis:
    """Test AI analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_backtest_result_success(self, analyzer, mock_db, sample_backtest_result):
        """Test successful AI analysis"""
        # Mock AI provider
        mock_provider = Mock()
        mock_provider.chat = AsyncMock(return_value='{"strengths": ["Good Sharpe"], "weaknesses": ["High drawdown"], "recommendations": ["Optimize parameters"]}')
        
        with patch('services.strategy_analyzer.get_default_model') as mock_model, \
             patch('services.strategy_analyzer.create_provider') as mock_provider_func:
            mock_model.return_value = Mock(is_active=True)
            mock_provider_func.return_value = mock_provider
            
            result = await analyzer.analyze_backtest_result(
                backtest_result=sample_backtest_result,
                strategy_code="test code",
                strategy_name="Test Strategy"
            )
            
            assert 'ai_analysis' in result
            assert 'structured_analysis' in result
            assert 'recommendations' in result
            assert mock_provider.chat.called
    
    @pytest.mark.asyncio
    async def test_analyze_backtest_result_no_ai(self, analyzer, mock_db, sample_backtest_result):
        """Test analysis when AI is not available"""
        with patch('services.strategy_analyzer.get_default_model', return_value=None):
            result = await analyzer.analyze_backtest_result(
                backtest_result=sample_backtest_result,
                strategy_code="test code",
                strategy_name="Test Strategy"
            )
            
            assert 'error' in result
            assert 'structured_analysis' in result
            assert result['structured_analysis'] is not None
    
    def test_parse_ai_response_json(self, analyzer):
        """Test parsing JSON AI response"""
        response = '{"strengths": ["A", "B"], "weaknesses": ["C"], "recommendations": ["D"]}'
        parsed = analyzer._parse_ai_response(response)
        
        assert 'strengths' in parsed
        assert len(parsed['strengths']) == 2
    
    def test_parse_ai_response_text(self, analyzer):
        """Test parsing text AI response"""
        response = "This is a text response without JSON"
        parsed = analyzer._parse_ai_response(response)
        
        assert 'raw_response' in parsed
        assert isinstance(parsed, dict)


class TestPromptCreation:
    """Test prompt creation for AI"""
    
    def test_create_analysis_prompt(self, analyzer, sample_backtest_result):
        """Test creating analysis prompt"""
        prompt = analyzer._create_analysis_prompt(
            backtest_result=sample_backtest_result,
            strategy_code="test code here",
            strategy_name="My Strategy"
        )
        
        assert isinstance(prompt, str)
        assert "My Strategy" in prompt
        assert "1.8" in prompt  # Sharpe ratio
        assert "15.5" in prompt  # Annual return
        assert len(prompt) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
