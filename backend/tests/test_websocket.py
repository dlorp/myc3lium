"""Tests for WebSocket connection manager"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websocket import ConnectionManager


@pytest.fixture
def manager():
    """Create a fresh ConnectionManager for each test"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket"""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect(manager, mock_websocket):
    """Test connecting a WebSocket client"""
    client_id = await manager.connect(mock_websocket)

    assert client_id.startswith("client_")
    assert mock_websocket.accept.called
    assert client_id in manager.active_connections
    assert manager.get_connection_count() == 1


@pytest.mark.asyncio
async def test_disconnect(manager, mock_websocket):
    """Test disconnecting a WebSocket client"""
    client_id = await manager.connect(mock_websocket)
    assert manager.get_connection_count() == 1

    manager.disconnect(client_id)

    assert client_id not in manager.active_connections
    assert manager.get_connection_count() == 0


@pytest.mark.asyncio
async def test_send_personal_message(manager, mock_websocket):
    """Test sending message to specific client"""
    client_id = await manager.connect(mock_websocket)

    message = {"event": "test", "data": {"value": 42}}
    await manager.send_personal_message(message, client_id)

    mock_websocket.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_send_personal_message_invalid_client(manager):
    """Test sending message to non-existent client"""
    # Should not raise an error
    await manager.send_personal_message({"event": "test"}, "invalid_client")


@pytest.mark.asyncio
async def test_send_personal_message_disconnected_client(manager, mock_websocket):
    """Test sending message to disconnected client cleans up"""
    client_id = await manager.connect(mock_websocket)

    # Simulate send failure
    mock_websocket.send_json.side_effect = Exception("Connection closed")

    await manager.send_personal_message({"event": "test"}, client_id)

    # Client should be removed
    assert client_id not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast(manager):
    """Test broadcasting to multiple clients"""
    # Connect multiple clients
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    await manager.connect(ws1)
    await manager.connect(ws2)

    message = {"event": "broadcast", "data": "test"}
    await manager.broadcast(message)

    ws1.send_json.assert_called_once_with(message)
    ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_with_exclude(manager):
    """Test broadcasting with exclusion list"""
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    client1 = await manager.connect(ws1)
    await manager.connect(ws2)

    message = {"event": "broadcast", "data": "test"}
    await manager.broadcast(message, exclude={client1})

    ws1.send_json.assert_not_called()
    ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_cleans_disconnected(manager):
    """Test broadcast removes disconnected clients"""
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()
    ws2.send_json.side_effect = Exception("Disconnected")

    client1 = await manager.connect(ws1)
    client2 = await manager.connect(ws2)

    assert manager.get_connection_count() == 2

    await manager.broadcast({"event": "test"})

    # Client2 should be removed due to send failure
    assert client1 in manager.active_connections
    assert client2 not in manager.active_connections
    assert manager.get_connection_count() == 1


@pytest.mark.asyncio
async def test_multiple_connections(manager):
    """Test managing multiple simultaneous connections"""
    clients = []

    for i in range(5):
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        client_id = await manager.connect(ws)
        clients.append(client_id)

    assert manager.get_connection_count() == 5
    assert all(client in manager.active_connections for client in clients)

    # Disconnect some
    manager.disconnect(clients[0])
    manager.disconnect(clients[2])

    assert manager.get_connection_count() == 3
    assert clients[0] not in manager.active_connections
    assert clients[1] in manager.active_connections
    assert clients[2] not in manager.active_connections
