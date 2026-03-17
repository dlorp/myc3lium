"""Pytest configuration and fixtures for test isolation"""

import pytest

from app.routers import nodes
from app.services.mock_data import MockMeshDataSource


@pytest.fixture(autouse=True)
def reset_mesh_store():
    """Reset mesh store to default mock state before each test

    This ensures test isolation by resetting mock data between tests.
    Without this, deleted/modified nodes/messages/threads persist across tests
    causing count mismatches and data leakage.

    Reloads the same mock data set that main.py uses for consistency.
    """
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

    # Cleanup after test (ensures clean slate for next test)
    if nodes.mesh_store:
        nodes.mesh_store.clear()
