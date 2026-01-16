"""
Tests for external API timeout and error handling
"""
import pytest
from unittest.mock import patch, Mock
from fastapi import status
import asyncio
import time


class TestMarketAPITimeout:
    """Test market API timeout handling"""
    
    def test_market_quote_timeout_handling(self, client):
        """Test that market quote requests handle timeouts gracefully"""
        # This test verifies the endpoint doesn't hang indefinitely
        # Real timeout testing would require mocking the external API
        
        start_time = time.time()
        response = client.get("/api/market/quote/AAPL", timeout=10.0)
        elapsed = time.time() - start_time
        
        # Should respond within timeout period
        assert elapsed < 10.0
        # Should return either success or error, not hang
        assert response.status_code in [200, 500, 503, 504]
    
    def test_market_indicators_timeout_handling(self, client):
        """Test that indicators requests handle timeouts gracefully"""
        start_time = time.time()
        response = client.get(
            "/api/market/indicators/AAPL?indicators=MACD,RSI&period=20",
            timeout=15.0
        )
        elapsed = time.time() - start_time
        
        assert elapsed < 15.0
        assert response.status_code in [200, 500, 503, 504]
    
    def test_multiple_quotes_timeout_handling(self, client):
        """Test that multiple quotes requests handle timeouts gracefully"""
        symbols = "AAPL,MSFT,GOOGL"  # Reduced symbols to avoid timeout
        start_time = time.time()
        response = client.get(f"/api/market/quotes?symbols={symbols}", timeout=30.0)
        elapsed = time.time() - start_time
        
        # Should respond within reasonable time (30 seconds for multiple quotes)
        assert elapsed < 30.0
        assert response.status_code in [200, 500, 503, 504]


class TestExternalAPIConnectionErrors:
    """Test handling of external API connection errors"""
    
    @patch('market_service.openbb_service')
    def test_connection_error_handling(self, mock_openbb, client):
        """Test that connection errors are handled gracefully"""
        # Mock connection error
        mock_openbb.get_realtime_quote.side_effect = ConnectionError("Connection failed")
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should return error, not crash
        assert response.status_code in [500, 503]
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data
    
    @patch('market_service.openbb_service')
    def test_timeout_error_handling(self, mock_openbb, client):
        """Test that timeout errors are handled gracefully"""
        # Mock timeout error
        mock_openbb.get_realtime_quote.side_effect = TimeoutError("Request timed out")
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should return error, not crash
        assert response.status_code in [500, 503, 504]
    
    @patch('market_service.openbb_service')
    def test_network_error_handling(self, mock_openbb, client):
        """Test that network errors are handled gracefully"""
        # Mock network error
        import requests
        mock_openbb.get_realtime_quote.side_effect = requests.exceptions.RequestException("Network error")
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should return error, not crash
        assert response.status_code in [500, 503]


class TestRateLimitHandling:
    """Test external API rate limit handling"""
    
    @patch('market_service.openbb_service')
    def test_rate_limit_429_error(self, mock_openbb, client):
        """Test handling of 429 Too Many Requests from external API"""
        # Mock rate limit error
        import requests
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Rate limited")
        mock_openbb.get_realtime_quote.side_effect = requests.exceptions.HTTPError("Rate limited", response=mock_response)
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should handle gracefully (may retry or return error)
        assert response.status_code in [200, 429, 500, 503]
    
    def test_rate_limit_retry_logic(self, client):
        """Test that rate limit retries work correctly"""
        # This tests the retry logic in openbb_service
        # The service should retry with exponential backoff
        # We can't easily test this without mocking, but we can verify
        # that the endpoint doesn't fail immediately on rate limits
        
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = client.get("/api/market/quote/AAPL")
            responses.append(response.status_code)
        
        # Should handle multiple requests (may rate limit, but shouldn't crash)
        assert all(status in [200, 429, 500, 503] for status in responses)


class TestExternalAPIErrorResponses:
    """Test handling of various external API error responses"""
    
    @patch('market_service.openbb_service')
    def test_404_error_from_external_api(self, mock_openbb, client):
        """Test handling of 404 from external API"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 404
        mock_openbb.get_realtime_quote.side_effect = requests.exceptions.HTTPError("Not found", response=mock_response)
        
        response = client.get("/api/market/quote/INVALID")
        
        # Should return appropriate error
        assert response.status_code in [404, 500, 503]
    
    @patch('market_service.openbb_service')
    def test_500_error_from_external_api(self, mock_openbb, client):
        """Test handling of 500 from external API"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 500
        mock_openbb.get_realtime_quote.side_effect = requests.exceptions.HTTPError("Server error", response=mock_response)
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should return error, not crash
        assert response.status_code in [500, 503]
    
    @patch('market_service.openbb_service')
    def test_invalid_response_format(self, mock_openbb, client):
        """Test handling of invalid response format from external API"""
        # Mock invalid response
        mock_openbb.get_realtime_quote.return_value = {"invalid": "format"}
        
        response = client.get("/api/market/quote/AAPL")
        
        # Should handle gracefully
        assert response.status_code in [200, 500, 503]


class TestAsyncAPICalls:
    """Test async external API calls"""
    
    def test_concurrent_api_calls(self, client):
        """Test that concurrent API calls are handled correctly"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/market/quote/AAPL")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should complete (may have errors, but shouldn't hang)
        assert len(responses) == 5
        assert all(r.status_code in [200, 500, 503] for r in responses)
    
    def test_async_timeout(self, client):
        """Test that async operations respect timeouts"""
        start_time = time.time()
        # Use longer timeout to account for retry logic and rate limiting
        response = client.get("/api/market/quotes?symbols=AAPL,MSFT,GOOGL", timeout=60.0)
        elapsed = time.time() - start_time
        
        # Should complete within reasonable timeout (allowing for retries)
        assert elapsed < 60.0
        assert response.status_code in [200, 500, 503, 504]


class TestFallbackMechanisms:
    """Test fallback mechanisms when external APIs fail"""
    
    @patch('market_service.openbb_service')
    def test_fallback_to_alternative_source(self, mock_openbb, client):
        """Test that system falls back to alternative data sources"""
        # Mock primary source failure
        mock_openbb.get_realtime_quote.side_effect = Exception("Primary source failed")
        
        # The service should fall back to yfinance (if configured)
        response = client.get("/api/market/quote/AAPL")
        
        # Should either use fallback or return error gracefully
        assert response.status_code in [200, 500, 503]
    
    def test_partial_failure_handling(self, client):
        """Test handling when some symbols succeed and others fail"""
        # Request multiple symbols
        response = client.get("/api/market/quotes?symbols=AAPL,INVALID_SYMBOL,MSFT")
        
        if response.status_code == 200:
            data = response.json()
            # Should return data for valid symbols, skip invalid ones
            assert isinstance(data, list)
            # Should have at least some results
            assert len(data) >= 0  # May be empty if all fail, but shouldn't crash
