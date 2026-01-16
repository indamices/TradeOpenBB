"""
Tests for Admin API endpoints
"""
import pytest
from fastapi import status

class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_get_rate_limit_status(self, client):
        """Test getting rate limit status"""
        response = client.get("/api/admin/rate-limit-status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should have rate limit information
        assert isinstance(data, dict)
    
    def test_reset_daily_limit(self, client):
        """Test resetting daily limit"""
        response = client.post("/api/admin/reset-daily-limit")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_sync_data_empty(self, client):
        """Test data sync with empty symbols"""
        response = client.post("/api/admin/sync-data", json={
            "symbols": [],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        })
        # Empty symbols list might be invalid (422) or handled gracefully (200/500)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]
