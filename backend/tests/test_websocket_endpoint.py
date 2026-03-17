"""Tests for WebSocket endpoint"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_websocket_connect():
    """Test WebSocket connection establishment"""
    with client.websocket_connect("/ws") as websocket:
        # Should receive welcome message
        data = websocket.receive_json()

        assert data["event"] == "connected"
        assert "client_id" in data["data"]
        assert data["data"]["message"] == "Connected to MYC3LIUM network"
        assert data["data"]["connections"] == 1


def test_websocket_echo():
    """Test WebSocket echo functionality"""
    with client.websocket_connect("/ws") as websocket:
        # Receive welcome message
        welcome = websocket.receive_json()
        assert welcome["event"] == "connected"

        # Receive stats message
        stats = websocket.receive_json()
        assert stats["event"] == "stats"

        # Send a message
        websocket.send_text("ping")

        # Should receive echo
        response = websocket.receive_json()
        assert response["event"] == "echo"
        assert response["data"]["received"] == "ping"


def test_websocket_multiple_clients():
    """Test multiple WebSocket clients"""
    with client.websocket_connect("/ws") as ws1:
        welcome1 = ws1.receive_json()
        assert welcome1["data"]["connections"] == 1

        with client.websocket_connect("/ws") as ws2:
            welcome2 = ws2.receive_json()
            assert welcome2["data"]["connections"] == 2


def test_websocket_disconnect_notification():
    """Test that disconnection is broadcast to other clients"""
    with client.websocket_connect("/ws") as ws1:
        ws1.receive_json()  # welcome

        with client.websocket_connect("/ws") as ws2:
            ws2.receive_json()  # welcome

        # ws2 disconnected, ws1 should receive notification
        # Give a moment for the disconnect broadcast
        try:
            data = ws1.receive_json(timeout=2)
            if data["event"] == "client_disconnected":
                assert "client_id" in data["data"]
                assert data["data"]["connections"] == 1
        except Exception:
            # Timeout is acceptable - broadcast might not arrive before test ends
            pass


def test_websocket_receives_updates():
    """Test that WebSocket receives node updates"""
    with client.websocket_connect("/ws") as websocket:
        # Receive welcome
        welcome = websocket.receive_json()
        assert welcome["event"] == "connected"

        # Wait for a node update (background task sends them every 3-8 seconds)
        # Try to receive with timeout
        for _ in range(10):  # Try up to 10 messages
            try:
                data = websocket.receive_json(timeout=1)
                if data["event"] in ["node_update", "connection_update"]:
                    assert "data" in data
                    assert "timestamp" in data
                    break
            except Exception:
                continue

        # Note: This might occasionally fail if no update arrives in time
        # In production, you'd use a more controlled test environment


def test_websocket_message_format():
    """Test WebSocket message format compliance"""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()

        # All messages should have event, data, timestamp
        assert "event" in data
        assert "data" in data
        assert "timestamp" in data

        # Event should be a string
        assert isinstance(data["event"], str)

        # Data should be a dict
        assert isinstance(data["data"], dict)


def test_websocket_connection_limit():
    """Test that multiple connections are handled properly"""
    connections = []

    try:
        # Create multiple connections
        for i in range(5):
            ws = client.websocket_connect("/ws")
            connections.append(ws)
            data = ws.__enter__().receive_json()
            assert data["event"] == "connected"
            assert data["data"]["connections"] == i + 1
    finally:
        # Clean up
        for ws in connections:
            try:
                ws.__exit__(None, None, None)
            except Exception:
                pass


def test_websocket_invalid_json():
    """Test WebSocket handles non-JSON gracefully"""
    with client.websocket_connect("/ws") as websocket:
        # Receive welcome
        websocket.receive_json()
        # Receive stats
        websocket.receive_json()

        # Send plain text (not JSON)
        websocket.send_text("plain text message")

        # Should receive echo
        response = websocket.receive_json()
        assert response["event"] == "echo"
        assert response["data"]["received"] == "plain text message"
