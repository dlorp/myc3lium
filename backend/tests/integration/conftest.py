"""Pytest configuration for integration tests"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import nodes


@pytest.fixture
def client():
    """FastAPI test client for integration tests"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_mesh_store():
    """Reset mesh store to default mock state before each test

    This ensures test isolation by resetting mock data between tests.
    """
    from app.services.mock_data import MockMeshDataSource

    # Reload mock data before each test
    if nodes.mesh_store:
        nodes.mesh_store.clear()
        mock_source = MockMeshDataSource(seed=42)
        nodes.mesh_store.load_from_source(
            mock_source.get_nodes(),
            mock_source.get_threads(),
            mock_source.get_messages(),
        )

    yield

    # Cleanup after test
    if nodes.mesh_store:
        nodes.mesh_store.clear()
