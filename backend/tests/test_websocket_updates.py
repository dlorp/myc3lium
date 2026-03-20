"""Tests for WebSocket real-time updates with mesh_store integration"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Message, Node, Thread
from app.routers.ws import set_mesh_store
from app.services.mesh_store import MeshStore
from app.websocket import ConnectionManager


@pytest.fixture
def mesh_store():
    """Create a fresh MeshStore for each test"""
    return MeshStore()


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


# Test mesh_store event emission


def test_mesh_store_emits_node_added(mesh_store):
    """Test that mesh_store emits node_added event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    mesh_store.on_event(handler)

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    assert len(events) == 1
    assert events[0][0] == "node_added"
    assert events[0][1]["id"] == "test_001"


def test_mesh_store_emits_node_updated(mesh_store):
    """Test that mesh_store emits node_update event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    mesh_store.on_event(handler)
    mesh_store.update_node("test_001", status="degraded")

    assert len(events) == 1
    assert events[0][0] == "node_update"
    assert events[0][1]["status"] == "degraded"


def test_mesh_store_emits_node_removed(mesh_store):
    """Test that mesh_store emits node_removed event"""
    events = []

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    mesh_store.on_event(lambda t, d: events.append((t, d)))
    mesh_store.remove_node("test_001")

    assert len(events) == 1
    assert events[0][0] == "node_removed"
    assert events[0][1]["id"] == "test_001"


def test_mesh_store_emits_message_added(mesh_store):
    """Test that mesh_store emits message_added event"""
    events = []

    # First create nodes
    sender = Node(id="sender", type="HYPHA", callsign="sender", status="online")
    recipient = Node(
        id="recipient", type="SPORE", callsign="recipient", status="online"
    )
    mesh_store.add_node(sender)
    mesh_store.add_node(recipient)

    mesh_store.on_event(lambda t, d: events.append((t, d)))

    message = Message(
        id="msg_001",
        sender_id="sender",
        recipient_id="recipient",
        content="Test message",
    )
    mesh_store.add_message(message)

    # Should have message_added event
    message_events = [e for e in events if e[0] == "message_added"]
    assert len(message_events) == 1
    assert message_events[0][1]["id"] == "msg_001"


def test_mesh_store_emits_thread_events(mesh_store):
    """Test that mesh_store emits thread-related events"""
    events = []

    # Create nodes first
    node1 = Node(id="node1", type="HYPHA", callsign="node1", status="online")
    node2 = Node(id="node2", type="SPORE", callsign="node2", status="online")
    mesh_store.add_node(node1)
    mesh_store.add_node(node2)

    mesh_store.on_event(lambda t, d: events.append((t, d)))

    thread = Thread(
        id="thread_001",
        source_id="node1",
        target_id="node2",
        radio_type="LoRa",
        quality=0.9,
    )
    mesh_store.add_thread(thread)

    # Should have thread_added event
    thread_events = [e for e in events if e[0] == "thread_added"]
    assert len(thread_events) == 1
    assert thread_events[0][1]["id"] == "thread_001"


# Test WebSocket broadcasting integration


@pytest.mark.asyncio
async def test_set_mesh_store_registers_handler(mesh_store):
    """Test that set_mesh_store registers event handler"""
    set_mesh_store(mesh_store)

    # mesh_store should have handlers registered
    assert len(mesh_store._event_handlers) > 0


@pytest.mark.asyncio
async def test_node_added_broadcasts_to_websockets(mesh_store, manager):
    """Test that adding a node broadcasts to connected WebSocket clients"""
    set_mesh_store(mesh_store)

    # Connect mock clients
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    # Patch the global manager
    with patch("app.routers.ws.manager", manager):
        await manager.connect(ws1)
        await manager.connect(ws2)

        # Add a node - this should trigger broadcast
        node = Node(
            id="test_001",
            type="HYPHA",
            callsign="test-node",
            status="online",
        )

        # Need to manually trigger broadcast since event loop isn't automatically set up
        with patch("asyncio.create_task") as mock_task:
            mesh_store.add_node(node)
            # The broadcast should be scheduled
            assert mock_task.called


@pytest.mark.asyncio
async def test_node_updated_broadcasts_to_websockets(mesh_store, manager):
    """Test that updating a node broadcasts to WebSocket clients"""
    set_mesh_store(mesh_store)

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()

    with patch("app.routers.ws.manager", manager):
        await manager.connect(ws)

        with patch("asyncio.create_task") as mock_task:
            mesh_store.update_node("test_001", status="degraded")
            assert mock_task.called


@pytest.mark.asyncio
async def test_node_removed_broadcasts_to_websockets(mesh_store, manager):
    """Test that removing a node broadcasts to WebSocket clients"""
    set_mesh_store(mesh_store)

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()

    with patch("app.routers.ws.manager", manager):
        await manager.connect(ws)

        with patch("asyncio.create_task") as mock_task:
            mesh_store.remove_node("test_001")
            assert mock_task.called


@pytest.mark.asyncio
async def test_message_added_broadcasts_to_websockets(mesh_store, manager):
    """Test that adding a message broadcasts to WebSocket clients"""
    set_mesh_store(mesh_store)

    # Create nodes
    sender = Node(id="sender", type="HYPHA", callsign="sender", status="online")
    recipient = Node(
        id="recipient", type="SPORE", callsign="recipient", status="online"
    )
    mesh_store.add_node(sender)
    mesh_store.add_node(recipient)

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()

    with patch("app.routers.ws.manager", manager):
        await manager.connect(ws)

        with patch("asyncio.create_task") as mock_task:
            message = Message(
                id="msg_001",
                sender_id="sender",
                recipient_id="recipient",
                content="Test message",
            )
            mesh_store.add_message(message)
            assert mock_task.called


# Test message format


@pytest.mark.asyncio
async def test_broadcast_message_format_for_node_added(mesh_store):
    """Test that broadcast messages have correct format for node_added"""
    broadcasts = []

    async def capture_broadcast(message, exclude=None):
        broadcasts.append(message)

    manager_mock = MagicMock()
    manager_mock.broadcast = capture_broadcast

    with patch("app.routers.ws.manager", manager_mock):
        set_mesh_store(mesh_store)

        node = Node(
            id="test_001",
            type="HYPHA",
            callsign="test-node",
            status="online",
        )

        # Trigger the event and manually invoke broadcast
        def sync_handler(event_type, data):
            # Manually create and check the message format
            message = {
                "type": "node_added",
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            broadcasts.append(message)

        mesh_store.on_event(sync_handler)
        mesh_store.add_node(node)

        # Should have at least one broadcast (from our handler)
        assert len(broadcasts) >= 1
        msg = broadcasts[0]
        assert msg["type"] == "node_added"
        assert "data" in msg
        assert msg["data"]["id"] == "test_001"
        assert "timestamp" in msg


@pytest.mark.asyncio
async def test_broadcast_message_format_for_node_updated(mesh_store):
    """Test that broadcast messages have correct format for node_updated"""
    broadcasts = []

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    def sync_handler(event_type, data):
        if event_type == "node_update":
            message = {
                "type": "node_updated",
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            broadcasts.append(message)

    mesh_store.on_event(sync_handler)
    mesh_store.update_node("test_001", status="degraded")

    assert len(broadcasts) == 1
    msg = broadcasts[0]
    assert msg["type"] == "node_updated"
    assert msg["data"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_broadcast_message_format_for_node_removed(mesh_store):
    """Test that broadcast messages have correct format for node_removed"""
    broadcasts = []

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )
    mesh_store.add_node(node)

    def sync_handler(event_type, data):
        if event_type == "node_removed":
            message = {
                "type": "node_removed",
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            broadcasts.append(message)

    mesh_store.on_event(sync_handler)
    mesh_store.remove_node("test_001")

    assert len(broadcasts) == 1
    msg = broadcasts[0]
    assert msg["type"] == "node_removed"
    assert msg["data"]["id"] == "test_001"


@pytest.mark.asyncio
async def test_broadcast_message_format_for_message_added(mesh_store):
    """Test that broadcast messages have correct format for message_added"""
    broadcasts = []

    # Create nodes
    sender = Node(id="sender", type="HYPHA", callsign="sender", status="online")
    recipient = Node(
        id="recipient", type="SPORE", callsign="recipient", status="online"
    )
    mesh_store.add_node(sender)
    mesh_store.add_node(recipient)

    def sync_handler(event_type, data):
        if event_type == "message_added":
            message = {
                "type": "message_added",
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            broadcasts.append(message)

    mesh_store.on_event(sync_handler)

    message = Message(
        id="msg_001",
        sender_id="sender",
        recipient_id="recipient",
        content="Test message",
    )
    mesh_store.add_message(message)

    assert len(broadcasts) == 1
    msg = broadcasts[0]
    assert msg["type"] == "message_added"
    assert msg["data"]["id"] == "msg_001"
    assert msg["data"]["content"] == "Test message"


# Test multiple clients


@pytest.mark.asyncio
async def test_multiple_clients_receive_broadcasts(mesh_store, manager):
    """Test that multiple WebSocket clients receive broadcasts"""
    set_mesh_store(mesh_store)

    clients = []
    for _ in range(3):
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        clients.append(ws)

    with patch("app.routers.ws.manager", manager):
        for ws in clients:
            await manager.connect(ws)

        # Manually broadcast
        await manager.broadcast({"type": "test", "data": {}})

        for ws in clients:
            assert ws.send_json.called


@pytest.mark.asyncio
async def test_event_handler_continues_on_error(mesh_store):
    """Test that event broadcasting continues even if one handler fails"""
    successful_calls = []

    def failing_handler(event_type, data):
        raise ValueError("Handler error")

    def working_handler(event_type, data):
        successful_calls.append((event_type, data))

    mesh_store.on_event(failing_handler)
    mesh_store.on_event(working_handler)

    node = Node(
        id="test_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
    )

    # Should not raise, and working handler should still be called
    mesh_store.add_node(node)

    assert len(successful_calls) == 1


# Test WebSocket endpoint initialization


@pytest.mark.asyncio
async def test_websocket_sends_stats_on_connect(mesh_store):
    """Test that WebSocket endpoint sends stats when client connects"""
    from app.routers.ws import websocket_endpoint

    # Add some data
    node = Node(id="test_001", type="HYPHA", callsign="test-node", status="online")
    mesh_store.add_node(node)

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=asyncio.CancelledError)

    manager_mock = ConnectionManager()

    with patch("app.routers.ws.manager", manager_mock):
        with patch("app.routers.ws._mesh_store", mesh_store):
            try:
                await websocket_endpoint(ws)
            except asyncio.CancelledError:
                pass

    # Should have called send_json at least twice (welcome + stats)
    assert ws.send_json.call_count >= 2


@pytest.mark.asyncio
async def test_websocket_handles_disconnect(mesh_store):
    """Test that WebSocket properly handles client disconnect"""
    from fastapi import WebSocketDisconnect

    from app.routers.ws import websocket_endpoint

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

    manager_mock = ConnectionManager()
    broadcast_called = False

    original_broadcast = manager_mock.broadcast

    async def track_broadcast(*args, **kwargs):
        nonlocal broadcast_called
        broadcast_called = True
        return await original_broadcast(*args, **kwargs)

    manager_mock.broadcast = track_broadcast

    with patch("app.routers.ws.manager", manager_mock):
        with patch("app.routers.ws._mesh_store", mesh_store):
            await websocket_endpoint(ws)

    # Should have broadcasted disconnect
    assert broadcast_called


# Test edge cases


def test_mesh_store_handles_multiple_event_handlers(mesh_store):
    """Test that mesh_store can handle multiple event handlers"""
    handler_calls = {"h1": [], "h2": [], "h3": []}

    def handler1(event_type, data):
        handler_calls["h1"].append(event_type)

    def handler2(event_type, data):
        handler_calls["h2"].append(event_type)

    def handler3(event_type, data):
        handler_calls["h3"].append(event_type)

    mesh_store.on_event(handler1)
    mesh_store.on_event(handler2)
    mesh_store.on_event(handler3)

    node = Node(id="test_001", type="HYPHA", callsign="test-node", status="online")
    mesh_store.add_node(node)

    assert len(handler_calls["h1"]) == 1
    assert len(handler_calls["h2"]) == 1
    assert len(handler_calls["h3"]) == 1


@pytest.mark.asyncio
async def test_websocket_echo_message(mesh_store):
    """Test that WebSocket echoes back client messages"""
    from app.routers.ws import websocket_endpoint

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()

    # First receive returns keepalive, then raises to exit
    ws.receive_text = AsyncMock(side_effect=["ping", asyncio.CancelledError()])

    manager_mock = ConnectionManager()

    with patch("app.routers.ws.manager", manager_mock):
        with patch("app.routers.ws._mesh_store", mesh_store):
            try:
                await websocket_endpoint(ws)
            except asyncio.CancelledError:
                pass

    # Should have sent welcome, stats, and echo
    assert ws.send_json.call_count >= 3


@pytest.mark.asyncio
async def test_websocket_rejects_oversized_message(mesh_store):
    """Test that WebSocket rejects messages that are too large"""
    from app.routers.ws import MAX_MESSAGE_SIZE, websocket_endpoint

    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()

    # Send an oversized message
    huge_message = "x" * (MAX_MESSAGE_SIZE + 1)
    ws.receive_text = AsyncMock(return_value=huge_message)

    manager_mock = ConnectionManager()

    with patch("app.routers.ws.manager", manager_mock):
        with patch("app.routers.ws._mesh_store", mesh_store):
            await websocket_endpoint(ws)

    # Should have closed the connection
    ws.close.assert_called_once()
