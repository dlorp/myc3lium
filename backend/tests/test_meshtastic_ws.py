"""Tests for the Meshtastic WebSocket endpoint and router security."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.routers import meshtastic
from app.services.meshtastic_service import MeshtasticStatus
from app.websocket import ConnectionManager


@pytest.fixture
def app():
    """Create a FastAPI app with the meshtastic router."""
    test_app = FastAPI()
    test_app.include_router(meshtastic.router)
    return test_app


@pytest.fixture
def client(app):
    """Provide a TestClient for the app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_ws_manager():
    """Reset the ConnectionManager between tests."""
    meshtastic._meshtastic_ws_manager = ConnectionManager()
    yield
    meshtastic._meshtastic_ws_manager = ConnectionManager()


@pytest.fixture(autouse=True)
def mock_service():
    """Provide a mock MeshtasticService."""
    mock = MagicMock()
    mock.available = True
    mock.get_status.return_value = MeshtasticStatus(
        connected=True,
        node_id="!12345678",
        short_name="TEST",
        nodes_count=5,
    )
    meshtastic._service = mock
    yield mock
    meshtastic._service = None


@pytest.fixture(autouse=True)
def clear_api_key():
    """Ensure API_KEY is not set unless a test explicitly sets it."""
    original = meshtastic.API_KEY
    meshtastic.API_KEY = None
    yield
    meshtastic.API_KEY = original


def test_ws_connect_returns_initial_status(client):
    """WebSocket connection receives initial status message with expected fields."""
    with client.websocket_connect("/api/meshtastic/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"
        assert data["data"]["connected"] is True
        assert data["data"]["node_id"] == "!12345678"
        assert data["data"]["short_name"] == "TEST"
        assert data["data"]["nodes_count"] == 5


def test_ws_connection_limit(client):
    """ConnectionManager rejects connections beyond MAX_CONNECTIONS."""
    meshtastic._meshtastic_ws_manager.MAX_CONNECTIONS = 2

    try:
        with client.websocket_connect("/api/meshtastic/ws") as ws1:
            ws1.receive_json()  # consume initial status
            with client.websocket_connect("/api/meshtastic/ws") as ws2:
                ws2.receive_json()  # consume initial status
                # Third connection should be rejected
                with pytest.raises(Exception):
                    with client.websocket_connect("/api/meshtastic/ws") as ws3:
                        ws3.receive_json()
    finally:
        meshtastic._meshtastic_ws_manager.MAX_CONNECTIONS = 100


def test_ws_message_size_validation(client):
    """Messages exceeding 1024 bytes return an error response."""
    with client.websocket_connect("/api/meshtastic/ws") as ws:
        ws.receive_json()  # consume initial status
        # Send a message exceeding 1024 bytes
        large_message = "X" * 1025
        ws.send_text(large_message)
        response = ws.receive_json()
        assert response["type"] == "error"
        assert "too large" in response["data"]["message"].lower()


def test_ws_auth_rejects_bad_token(client):
    """WebSocket rejects connections with invalid or missing token when key is set."""
    meshtastic.API_KEY = "secret123"

    # No token provided
    with pytest.raises(Exception):
        with client.websocket_connect("/api/meshtastic/ws") as ws:
            ws.receive_json()

    # Wrong token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/meshtastic/ws?token=wrong") as ws:
            ws.receive_json()


def test_ws_auth_accepts_valid_token(client):
    """WebSocket accepts connection with correct token."""
    meshtastic.API_KEY = "secret123"
    with client.websocket_connect("/api/meshtastic/ws?token=secret123") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"
        assert data["data"]["connected"] is True


def test_ws_auth_skipped_when_no_key(client):
    """WebSocket allows connection without token when no API key is configured."""
    # clear_api_key_env fixture already ensures MESHTASTIC_API_KEY is unset
    with client.websocket_connect("/api/meshtastic/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"
        assert data["data"]["connected"] is True


@pytest.mark.asyncio
async def test_ws_broadcast_delivers_to_clients(app):
    """Broadcast via _broadcast_to_websockets_internal reaches connected clients."""
    client = TestClient(app)
    with client.websocket_connect("/api/meshtastic/ws") as ws:
        ws.receive_json()  # consume initial status

        # Broadcast a message through the manager
        await meshtastic._broadcast_to_websockets_internal(
            "test_event", {"key": "value"}
        )

        data = ws.receive_json()
        assert data["type"] == "test_event"
        assert data["data"]["key"] == "value"


def test_send_error_does_not_leak_details(client, mock_service):
    """POST /send returns generic error without leaking internal details."""
    mock_service.send_message.side_effect = RuntimeError(
        "serial port /dev/ttyUSB1 closed"
    )

    # The send endpoint requires API key auth; patch verify_api_key to pass through
    with patch("app.routers.meshtastic.verify_api_key", return_value="testkey"):
        with patch("app.routers.meshtastic.send_limiter", return_value=True):
            response = client.post(
                "/api/meshtastic/send",
                json={"text": "hello", "channel": 0},
                headers={"X-API-Key": "testkey"},
            )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "serial" not in detail.lower()
    assert "ttyUSB1" not in detail
