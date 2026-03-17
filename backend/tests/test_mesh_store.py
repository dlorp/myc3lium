"""Tests for mesh store CRUD operations"""

from datetime import UTC, datetime

import pytest

from app.models import Message, Node, Thread
from app.services.mesh_store import MeshStore


@pytest.fixture
def store():
    """Create a fresh mesh store for each test"""
    return MeshStore()


@pytest.fixture
def sample_nodes():
    """Create sample nodes for testing"""
    return [
        Node(
            id="node_001",
            type="HYPHA",
            callsign="TEST-NODE-1",
            status="online",
            rssi=-65,
            battery=85,
        ),
        Node(
            id="node_002",
            type="SPORE",
            callsign="TEST-NODE-2",
            status="online",
            rssi=-70,
            battery=60,
        ),
        Node(
            id="node_003",
            type="FROND",
            callsign="TEST-NODE-3",
            status="degraded",
            rssi=-85,
            battery=20,
        ),
    ]


@pytest.fixture
def sample_threads(sample_nodes):
    """Create sample threads for testing"""
    return [
        Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type="LoRa",
            rssi=-72,
            quality=0.85,
            latency=25,
        ),
        Thread(
            id="thread_002",
            source_id="node_002",
            target_id="node_003",
            radio_type="WiFi",
            rssi=-65,
            quality=0.92,
            latency=15,
        ),
    ]


@pytest.fixture
def sample_messages(sample_nodes):
    """Create sample messages for testing"""
    return [
        Message(
            id="msg_001",
            sender_id="node_001",
            recipient_id="node_002",
            content="Test message 1",
            hops=1,
        ),
        Message(
            id="msg_002",
            sender_id="node_002",
            recipient_id="node_003",
            content="Test message 2",
            hops=2,
        ),
    ]


# Node CRUD tests
def test_add_node(store, sample_nodes):
    """Test adding a node"""
    node = sample_nodes[0]
    added = store.add_node(node)

    assert added.id == node.id
    assert store.get_node(node.id) == node


def test_add_duplicate_node(store, sample_nodes):
    """Test that adding duplicate node raises error"""
    node = sample_nodes[0]
    store.add_node(node)

    with pytest.raises(ValueError, match="already exists"):
        store.add_node(node)


def test_get_node(store, sample_nodes):
    """Test getting a node by ID"""
    node = sample_nodes[0]
    store.add_node(node)

    retrieved = store.get_node(node.id)
    assert retrieved == node


def test_get_nonexistent_node(store):
    """Test getting a node that doesn't exist"""
    result = store.get_node("nonexistent")
    assert result is None


def test_get_all_nodes(store, sample_nodes):
    """Test getting all nodes"""
    for node in sample_nodes:
        store.add_node(node)

    all_nodes = store.get_all_nodes()
    assert len(all_nodes) == len(sample_nodes)
    assert set(n.id for n in all_nodes) == set(n.id for n in sample_nodes)


def test_update_node(store, sample_nodes):
    """Test updating a node"""
    node = sample_nodes[0]
    store.add_node(node)

    updated = store.update_node(node.id, status="degraded", battery=50)

    assert updated is not None
    assert updated.status == "degraded"
    assert updated.battery == 50
    assert updated.id == node.id  # ID unchanged


def test_update_nonexistent_node(store):
    """Test updating a node that doesn't exist"""
    result = store.update_node("nonexistent", status="offline")
    assert result is None


def test_remove_node(store, sample_nodes):
    """Test removing a node"""
    node = sample_nodes[0]
    store.add_node(node)

    result = store.remove_node(node.id)
    assert result is True
    assert store.get_node(node.id) is None


def test_remove_nonexistent_node(store):
    """Test removing a node that doesn't exist"""
    result = store.remove_node("nonexistent")
    assert result is False


def test_remove_node_removes_threads(store, sample_nodes):
    """Test that removing a node also removes its threads"""
    # Add nodes
    for node in sample_nodes[:2]:
        store.add_node(node)

    # Add thread between nodes
    thread = Thread(
        id="thread_001",
        source_id=sample_nodes[0].id,
        target_id=sample_nodes[1].id,
        radio_type="LoRa",
        quality=0.8,
    )
    store.add_thread(thread)

    # Remove first node
    store.remove_node(sample_nodes[0].id)

    # Thread should be removed too
    assert store.get_thread(thread.id) is None


# Thread CRUD tests
def test_add_thread(store, sample_nodes, sample_threads):
    """Test adding a thread"""
    # Add nodes first
    for node in sample_nodes[:2]:
        store.add_node(node)

    thread = sample_threads[0]
    added = store.add_thread(thread)

    assert added.id == thread.id
    assert store.get_thread(thread.id) == thread


def test_add_thread_missing_source_node(store, sample_threads):
    """Test that adding thread with missing source node raises error"""
    thread = sample_threads[0]

    with pytest.raises(ValueError, match="Source node"):
        store.add_thread(thread)


def test_add_thread_missing_target_node(store, sample_nodes, sample_threads):
    """Test that adding thread with missing target node raises error"""
    # Only add source node
    store.add_node(sample_nodes[0])

    thread = sample_threads[0]

    with pytest.raises(ValueError, match="Target node"):
        store.add_thread(thread)


def test_add_duplicate_thread(store, sample_nodes, sample_threads):
    """Test that adding duplicate thread raises error"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    thread = sample_threads[0]
    store.add_thread(thread)

    with pytest.raises(ValueError, match="already exists"):
        store.add_thread(thread)


def test_get_thread(store, sample_nodes, sample_threads):
    """Test getting a thread by ID"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    thread = sample_threads[0]
    store.add_thread(thread)

    retrieved = store.get_thread(thread.id)
    assert retrieved == thread


def test_get_nonexistent_thread(store):
    """Test getting a thread that doesn't exist"""
    result = store.get_thread("nonexistent")
    assert result is None


def test_get_all_threads(store, sample_nodes, sample_threads):
    """Test getting all threads"""
    for node in sample_nodes:
        store.add_node(node)

    for thread in sample_threads:
        store.add_thread(thread)

    all_threads = store.get_all_threads()
    assert len(all_threads) == len(sample_threads)


def test_get_threads_for_node(store, sample_nodes, sample_threads):
    """Test getting threads for a specific node"""
    for node in sample_nodes:
        store.add_node(node)

    for thread in sample_threads:
        store.add_thread(thread)

    # node_002 is target of thread_001 and source of thread_002
    threads = store.get_threads_for_node("node_002")
    assert len(threads) == 2


def test_update_thread(store, sample_nodes, sample_threads):
    """Test updating a thread"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    thread = sample_threads[0]
    store.add_thread(thread)

    updated = store.update_thread(thread.id, quality=0.95, latency=10)

    assert updated is not None
    assert updated.quality == 0.95
    assert updated.latency == 10


def test_update_nonexistent_thread(store):
    """Test updating a thread that doesn't exist"""
    result = store.update_thread("nonexistent", quality=0.5)
    assert result is None


def test_remove_thread(store, sample_nodes, sample_threads):
    """Test removing a thread"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    thread = sample_threads[0]
    store.add_thread(thread)

    result = store.remove_thread(thread.id)
    assert result is True
    assert store.get_thread(thread.id) is None


def test_remove_nonexistent_thread(store):
    """Test removing a thread that doesn't exist"""
    result = store.remove_thread("nonexistent")
    assert result is False


# Message CRUD tests
def test_add_message(store, sample_nodes, sample_messages):
    """Test adding a message"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    message = sample_messages[0]
    added = store.add_message(message)

    assert added.id == message.id
    assert store.get_message(message.id) == message


def test_add_message_missing_sender(store, sample_messages):
    """Test that adding message with missing sender raises error"""
    message = sample_messages[0]

    with pytest.raises(ValueError, match="Sender node"):
        store.add_message(message)


def test_add_message_missing_recipient(store, sample_nodes, sample_messages):
    """Test that adding message with missing recipient raises error"""
    # Only add sender
    store.add_node(sample_nodes[0])

    message = sample_messages[0]

    with pytest.raises(ValueError, match="Recipient node"):
        store.add_message(message)


def test_add_broadcast_message(store, sample_nodes):
    """Test adding a broadcast message (no recipient)"""
    store.add_node(sample_nodes[0])

    message = Message(
        id="broadcast_001",
        sender_id=sample_nodes[0].id,
        recipient_id=None,
        content="Broadcast message",
    )

    added = store.add_message(message)
    assert added.recipient_id is None


def test_add_duplicate_message(store, sample_nodes, sample_messages):
    """Test that adding duplicate message raises error"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    message = sample_messages[0]
    store.add_message(message)

    with pytest.raises(ValueError, match="already exists"):
        store.add_message(message)


def test_get_message(store, sample_nodes, sample_messages):
    """Test getting a message by ID"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    message = sample_messages[0]
    store.add_message(message)

    retrieved = store.get_message(message.id)
    assert retrieved == message


def test_get_nonexistent_message(store):
    """Test getting a message that doesn't exist"""
    result = store.get_message("nonexistent")
    assert result is None


def test_get_all_messages(store, sample_nodes, sample_messages):
    """Test getting all messages sorted by timestamp"""
    for node in sample_nodes:
        store.add_node(node)

    for message in sample_messages:
        store.add_message(message)

    all_messages = store.get_all_messages()
    assert len(all_messages) == len(sample_messages)

    # Messages should be sorted newest first
    for i in range(len(all_messages) - 1):
        assert all_messages[i].timestamp >= all_messages[i + 1].timestamp


def test_get_messages_for_node(store, sample_nodes, sample_messages):
    """Test getting messages for a specific node"""
    for node in sample_nodes:
        store.add_node(node)

    for message in sample_messages:
        store.add_message(message)

    # node_002 is recipient of msg_001 and sender of msg_002
    messages = store.get_messages_for_node("node_002")
    assert len(messages) == 2


def test_remove_message(store, sample_nodes, sample_messages):
    """Test removing a message"""
    for node in sample_nodes[:2]:
        store.add_node(node)

    message = sample_messages[0]
    store.add_message(message)

    result = store.remove_message(message.id)
    assert result is True
    assert store.get_message(message.id) is None


def test_remove_nonexistent_message(store):
    """Test removing a message that doesn't exist"""
    result = store.remove_message("nonexistent")
    assert result is False


# Event emission tests
def test_event_emission_node_added(store, sample_nodes):
    """Test that adding a node emits event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    store.on_event(handler)
    node = sample_nodes[0]
    store.add_node(node)

    assert len(events) == 1
    assert events[0][0] == "node_added"
    assert events[0][1]["id"] == node.id


def test_event_emission_node_update(store, sample_nodes):
    """Test that updating a node emits event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    node = sample_nodes[0]
    store.add_node(node)

    store.on_event(handler)
    store.update_node(node.id, status="degraded")

    assert len(events) == 1
    assert events[0][0] == "node_update"
    assert events[0][1]["status"] == "degraded"


def test_event_emission_node_removed(store, sample_nodes):
    """Test that removing a node emits event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    node = sample_nodes[0]
    store.add_node(node)

    store.on_event(handler)
    store.remove_node(node.id)

    assert len(events) >= 1
    assert events[0][0] == "node_removed"
    assert events[0][1]["id"] == node.id


def test_event_handler_error_doesnt_stop_others(store, sample_nodes):
    """Test that error in one handler doesn't stop others"""
    events = []

    def bad_handler(event_type, data):
        raise Exception("Handler error")

    def good_handler(event_type, data):
        events.append((event_type, data))

    store.on_event(bad_handler)
    store.on_event(good_handler)

    node = sample_nodes[0]
    store.add_node(node)

    # Good handler should still receive event
    assert len(events) == 1


# Utility method tests
def test_clear_store(store, sample_nodes):
    """Test clearing all data from store"""
    for node in sample_nodes:
        store.add_node(node)

    store.clear()

    assert len(store.get_all_nodes()) == 0
    assert len(store.get_all_threads()) == 0
    assert len(store.get_all_messages()) == 0


def test_get_stats(store, sample_nodes):
    """Test getting store statistics"""
    for node in sample_nodes:
        store.add_node(node)

    stats = store.get_stats()

    assert stats["node_count"] == 3
    assert stats["active_node_count"] == 2  # 2 online nodes
    assert stats["thread_count"] == 0
    assert stats["message_count"] == 0
    assert "last_update" in stats


def test_load_from_source(store, sample_nodes, sample_threads, sample_messages):
    """Test bulk loading data from source"""
    store.load_from_source(sample_nodes, sample_threads, sample_messages)

    assert len(store.get_all_nodes()) == len(sample_nodes)
    assert len(store.get_all_threads()) == len(sample_threads)
    assert len(store.get_all_messages()) == len(sample_messages)


def test_load_from_source_emits_event(store, sample_nodes):
    """Test that load_from_source emits store_loaded event"""
    events = []

    def handler(event_type, data):
        events.append((event_type, data))

    store.on_event(handler)
    store.load_from_source(sample_nodes, [], [])

    # Should have store_loaded event
    assert any(e[0] == "store_loaded" for e in events)
