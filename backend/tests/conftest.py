"""Pytest configuration and fixtures for test isolation"""

import pytest
from app.routers import nodes


@pytest.fixture(autouse=True)
def reset_mock_nodes():
    """Reset mock nodes to empty state before each test
    
    This ensures test isolation by clearing mock data between tests.
    Without this, deleted/modified nodes persist across tests causing
    count mismatches and data leakage.
    
    The _generate_mock_data() function will repopulate the data on first
    API call in each test.
    """
    # Clear mock nodes before each test
    nodes._mock_nodes.clear()
    
    yield
    
    # Cleanup after test (ensures clean slate for next test)
    nodes._mock_nodes.clear()
