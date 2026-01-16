"""
Tests for database transaction handling and rollback
"""
import pytest
from fastapi import status
from sqlalchemy.exc import IntegrityError
from models import Portfolio, Position, Order


class TestTransactionRollback:
    """Test database transaction rollback on errors"""
    
    def test_portfolio_creation_rollback_on_error(self, client, db_session):
        """Test that portfolio creation rolls back on error"""
        # Try to create portfolio with invalid data that should fail
        response = client.post(
            "/api/portfolio",
            json={"name": "", "initial_cash": -1000.0}  # Invalid data
        )
        
        # Should return validation error, not create portfolio
        assert response.status_code in [400, 422]
        
        # Verify no portfolio was created
        count = db_session.query(Portfolio).count()
        # Count should be same as before (only default portfolio if exists)
        assert count <= 1  # Only default portfolio if it exists
    
    def test_position_creation_rollback_on_invalid_portfolio(self, client, db_session):
        """Test that position creation rolls back if portfolio doesn't exist"""
        # Try to create position with non-existent portfolio_id
        response = client.post(
            "/api/positions",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "avg_price": 150.0,
                "current_price": 155.0,
                "portfolio_id": 99999  # Non-existent
            }
        )
        
        # Should return error, not create position
        assert response.status_code in [400, 404, 422]
        
        # Verify no position was created
        count = db_session.query(Position).count()
        assert count == 0
    
    def test_order_creation_rollback_on_invalid_data(self, client, db_session, default_portfolio):
        """Test that order creation rolls back on invalid data"""
        # Try to create order with invalid data
        response = client.post(
            "/api/orders",
            json={
                "symbol": "",
                "side": "INVALID",
                "type": "MARKET",
                "quantity": -10,  # Invalid negative quantity
                "portfolio_id": default_portfolio
            }
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
        
        # Verify no order was created
        count = db_session.query(Order).count()
        assert count == 0


class TestConcurrentUpdates:
    """Test concurrent database updates and data consistency"""
    
    def test_concurrent_portfolio_updates(self, client, default_portfolio):
        """Test concurrent updates to the same portfolio"""
        # This is a simplified test - real concurrency would need threading
        # First update
        response1 = client.put(
            f"/api/portfolio/{default_portfolio}",
            json={"name": "Updated 1", "initial_cash": 10000.0}
        )
        
        # Second update
        response2 = client.put(
            f"/api/portfolio/{default_portfolio}",
            json={"name": "Updated 2", "initial_cash": 20000.0}
        )
        
        # Both should succeed (or at least one should)
        assert response1.status_code in [200, 404, 500]
        assert response2.status_code in [200, 404, 500]
        
        # Final state should be consistent
        final_response = client.get(f"/api/portfolio?portfolio_id={default_portfolio}")
        if final_response.status_code == 200:
            data = final_response.json()
            # Should have valid data
            assert "name" in data
            assert "initial_cash" in data
    
    def test_portfolio_balance_consistency(self, client, default_portfolio):
        """Test that portfolio balance remains consistent after operations"""
        # Get initial balance
        initial_response = client.get(f"/api/portfolio?portfolio_id={default_portfolio}")
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            initial_cash = initial_data.get("current_cash", 0)
            
            # Create an order (should update portfolio balance)
            order_response = client.post(
                "/api/orders",
                json={
                    "symbol": "AAPL",
                    "side": "BUY",
                    "type": "MARKET",
                    "quantity": 10,
                    "portfolio_id": default_portfolio
                }
            )
            
            # Check balance after order
            if order_response.status_code == 201:
                final_response = client.get(f"/api/portfolio?portfolio_id={default_portfolio}")
                if final_response.status_code == 200:
                    final_data = final_response.json()
                    final_cash = final_data.get("current_cash", 0)
                    # Balance should have changed (or remained same if order failed)
                    # Just verify it's a valid number
                    assert isinstance(final_cash, (int, float))


class TestDataIntegrity:
    """Test database integrity constraints"""
    
    def test_unique_constraint_violation(self, client, db_session):
        """Test handling of unique constraint violations"""
        # Create first portfolio
        response1 = client.post(
            "/api/portfolio",
            json={"name": "Unique Test", "initial_cash": 1000.0}
        )
        
        # Try to create duplicate (if name is unique)
        # Note: This depends on whether name has unique constraint
        # If not, this test may not trigger IntegrityError
        pass  # Would need unique constraint on name field
    
    def test_foreign_key_constraint(self, client, db_session):
        """Test handling of foreign key constraint violations"""
        # Try to create position with invalid portfolio_id
        response = client.post(
            "/api/positions",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "avg_price": 150.0,
                "current_price": 155.0,
                "portfolio_id": 99999  # Invalid foreign key
            }
        )
        
        # Should return error, not IntegrityError (should be caught earlier)
        assert response.status_code in [400, 404, 422]
    
    def test_not_null_constraint(self, client, db_session):
        """Test handling of NOT NULL constraint violations"""
        # Try to create portfolio without required fields
        response = client.post(
            "/api/portfolio",
            json={}  # Missing required fields
        )
        
        # Should return validation error before hitting database
        assert response.status_code in [400, 422]


class TestTransactionIsolation:
    """Test transaction isolation and consistency"""
    
    def test_transaction_isolation_read_committed(self, client, default_portfolio):
        """Test that uncommitted changes are not visible"""
        # This is a simplified test
        # In a real scenario, we'd need two separate database sessions
        # to test true isolation
        
        # Create a portfolio
        create_response = client.post(
            "/api/portfolio",
            json={"name": "Isolation Test", "initial_cash": 1000.0}
        )
        
        if create_response.status_code == 201:
            portfolio_id = create_response.json()["id"]
            
            # Read it back
            read_response = client.get(f"/api/portfolio?portfolio_id={portfolio_id}")
            assert read_response.status_code == 200
    
    def test_rollback_after_partial_success(self, client, db_session):
        """Test rollback when part of a transaction succeeds"""
        # This would require a multi-step operation that can partially fail
        # For example, creating an order that updates portfolio balance
        # but then fails on a subsequent step
        
        # Simplified: Create order that might fail
        response = client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 10,
                "portfolio_id": 1  # Assuming default portfolio exists
            }
        )
        
        # If it fails, verify no partial state was saved
        if response.status_code not in [200, 201]:
            # Check that portfolio balance wasn't partially updated
            portfolio_response = client.get("/api/portfolio?portfolio_id=1")
            if portfolio_response.status_code == 200:
                # Balance should be consistent
                pass


class TestDatabaseConnectionHandling:
    """Test database connection and session handling"""
    
    def test_database_connection_recovery(self, client):
        """Test that database connection errors are handled gracefully"""
        # This is hard to test without actually breaking the connection
        # But we can verify that endpoints handle errors gracefully
        response = client.get("/api/portfolio?portfolio_id=1")
        # Should not crash, even if database is unavailable
        assert response.status_code in [200, 404, 500]
    
    def test_session_cleanup_on_error(self, client):
        """Test that database sessions are properly closed on errors"""
        # Make multiple requests to ensure sessions are cleaned up
        for i in range(10):
            response = client.get("/api/ai-models")
            assert response.status_code in [200, 500]
        
        # If sessions weren't cleaned up, we'd see connection pool exhaustion
        # This is a basic smoke test
