"""Comprehensive tests for message management endpoints"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models import Message, Node
from app.routers import nodes as nodes_router

client = TestClient(app)


def setup_test_nodes():
    """Helper to set up test nodes in the mesh store"""
    # Get the mesh_store from nodes router
    mesh_store = nodes_router.mesh_store

    # Clear existing data
    mesh_store.clear()

    # Add test nodes
    test_nodes = [
        Node(
            id="node_001",
            type="HYPHA",
            callsign="sender-alpha",
            status="online",
            last_seen=datetime.now(timezone.utc),
        ),
        Node(
            id="node_002",
            type="SPORE",
            callsign="recipient-beta",
            status="online",
            last_seen=datetime.now(timezone.utc),
        ),
        Node(
            id="node_003",
            type="FROND",
            callsign="relay-gamma",
            status="online",
            last_seen=datetime.now(timezone.utc),
        ),
    ]

    for node in test_nodes:
        mesh_store.add_node(node)


def setup_test_messages():
    """Helper to set up test messages in the mesh store"""
    setup_test_nodes()

    # Get the mesh_store from nodes router
    mesh_store = nodes_router.mesh_store

    test_messages = [
        Message(
            id="msg_001",
            sender_id="node_001",
            recipient_id="node_002",
            content="Test message 1",
            timestamp=datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc),
            hops=1,
        ),
        Message(
            id="msg_002",
            sender_id="node_002",
            recipient_id="node_001",
            content="Reply to message 1",
            timestamp=datetime(2026, 3, 16, 12, 1, 0, tzinfo=timezone.utc),
            hops=1,
        ),
        Message(
            id="msg_003",
            sender_id="node_001",
            recipient_id=None,
            content="Broadcast message",
            timestamp=datetime(2026, 3, 16, 12, 2, 0, tzinfo=timezone.utc),
            hops=0,
        ),
        Message(
            id="msg_004",
            sender_id="node_003",
            recipient_id="node_002",
            content="Message from relay",
            timestamp=datetime(2026, 3, 16, 12, 3, 0, tzinfo=timezone.utc),
            hops=2,
        ),
    ]

    for message in test_messages:
        mesh_store.add_message(message)


class TestGetMessages:
    """Tests for GET /api/messages"""

    def test_get_all_messages(self):
        """Test retrieving all messages without filters"""
        setup_test_messages()

        response = client.get("/api/messages")
        assert response.status_code == 200

        msgs = response.json()
        assert isinstance(msgs, list)
        assert len(msgs) == 4

    def test_messages_sorted_newest_first(self):
        """Test that messages are returned sorted by timestamp (newest first)"""
        setup_test_messages()

        response = client.get("/api/messages")
        msgs = response.json()

        timestamps = [msg["timestamp"] for msg in msgs]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_filter_by_sender(self):
        """Test filtering messages by sender_id"""
        setup_test_messages()

        response = client.get("/api/messages?sender_id=node_001")
        assert response.status_code == 200

        msgs = response.json()
        assert len(msgs) == 2
        for msg in msgs:
            assert msg["sender_id"] == "node_001"

    def test_filter_by_recipient(self):
        """Test filtering messages by recipient_id"""
        setup_test_messages()

        response = client.get("/api/messages?recipient_id=node_002")
        assert response.status_code == 200

        msgs = response.json()
        assert len(msgs) == 2
        for msg in msgs:
            assert msg["recipient_id"] == "node_002"

    def test_filter_by_sender_and_recipient(self):
        """Test filtering by both sender and recipient"""
        setup_test_messages()

        response = client.get("/api/messages?sender_id=node_001&recipient_id=node_002")
        assert response.status_code == 200

        msgs = response.json()
        assert len(msgs) == 1
        assert msgs[0]["id"] == "msg_001"

    def test_limit_parameter(self):
        """Test that limit parameter restricts result count"""
        setup_test_messages()

        response = client.get("/api/messages?limit=2")
        assert response.status_code == 200

        msgs = response.json()
        assert len(msgs) == 2

    def test_cursor_pagination(self):
        """Test cursor-based pagination"""
        setup_test_messages()

        response = client.get("/api/messages")
        msgs = response.json()

        cursor = msgs[0]["id"]

        response = client.get(f"/api/messages?cursor={cursor}")
        assert response.status_code == 200

        paginated_msgs = response.json()
        assert len(paginated_msgs) == 3
        assert cursor not in [m["id"] for m in paginated_msgs]

    def test_empty_result_when_no_matches(self):
        """Test that empty results are valid when filters match nothing"""
        setup_test_messages()

        response = client.get("/api/messages?sender_id=nonexistent_node")
        assert response.status_code == 200
        assert response.json() == []


class TestGetMessageById:
    """Tests for GET /api/messages/{message_id}"""

    def test_get_existing_message(self):
        """Test retrieving a specific message by ID"""
        setup_test_messages()

        response = client.get("/api/messages/msg_001")
        assert response.status_code == 200

        msg = response.json()
        assert msg["id"] == "msg_001"
        assert msg["sender_id"] == "node_001"
        assert msg["recipient_id"] == "node_002"

    def test_get_nonexistent_message(self):
        """Test retrieving a message that doesn't exist"""
        setup_test_messages()

        response = client.get("/api/messages/nonexistent_message")
        assert response.status_code == 404

    def test_get_broadcast_message(self):
        """Test retrieving a broadcast message"""
        setup_test_messages()

        response = client.get("/api/messages/msg_003")
        assert response.status_code == 200

        msg = response.json()
        assert msg["recipient_id"] is None


class TestCreateMessage:
    """Tests for POST /api/messages"""

    def test_create_message_with_recipient(self):
        """Test creating a message with a specific recipient"""
        setup_test_nodes()

        payload = {
            "sender_id": "node_001",
            "recipient_id": "node_002",
            "content": "New test message",
            "hops": 1,
        }

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 201

        msg = response.json()
        assert msg["sender_id"] == "node_001"
        assert msg["recipient_id"] == "node_002"
        assert "id" in msg
        assert "timestamp" in msg

    def test_create_broadcast_message(self):
        """Test creating a broadcast message (no recipient)"""
        setup_test_nodes()

        payload = {
            "sender_id": "node_001",
            "recipient_id": None,
            "content": "Broadcast to all nodes",
            "hops": 0,
        }

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 201

        msg = response.json()
        assert msg["recipient_id"] is None

    def test_create_message_generates_unique_id(self):
        """Test that created messages get unique IDs"""
        setup_test_nodes()

        payload = {"sender_id": "node_001", "content": "Message 1", "hops": 0}

        response1 = client.post("/api/messages", json=payload)
        response2 = client.post("/api/messages", json=payload)

        msg1 = response1.json()
        msg2 = response2.json()

        assert msg1["id"] != msg2["id"]

    def test_create_message_nonexistent_sender(self):
        """Test creating a message from nonexistent sender"""
        setup_test_nodes()

        payload = {
            "sender_id": "nonexistent_sender",
            "recipient_id": "node_002",
            "content": "Should fail",
            "hops": 0,
        }

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_create_message_nonexistent_recipient(self):
        """Test creating a message to nonexistent recipient"""
        setup_test_nodes()

        payload = {
            "sender_id": "node_001",
            "recipient_id": "nonexistent_recipient",
            "content": "Should fail",
            "hops": 0,
        }

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_create_message_missing_required_fields(self):
        """Test that missing required fields cause validation error"""
        setup_test_nodes()

        response = client.post(
            "/api/messages", json={"content": "No sender", "hops": 0}
        )
        assert response.status_code == 422

        response = client.post(
            "/api/messages", json={"sender_id": "node_001", "hops": 0}
        )
        assert response.status_code == 422

    def test_create_message_with_max_content_length(self):
        """Test creating a message with maximum content length"""
        setup_test_nodes()

        long_content = "A" * 1024
        payload = {"sender_id": "node_001", "content": long_content, "hops": 0}

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 201

    def test_create_message_exceeds_max_content_length(self):
        """Test that content exceeding max length causes validation error"""
        setup_test_nodes()

        too_long_content = "A" * 1025
        payload = {"sender_id": "node_001", "content": too_long_content, "hops": 0}

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 422

    def test_created_message_retrievable(self):
        """Test that created message can be retrieved"""
        setup_test_nodes()

        payload = {"sender_id": "node_001", "content": "Retrievable message", "hops": 0}

        create_response = client.post("/api/messages", json=payload)
        msg = create_response.json()
        msg_id = msg["id"]

        get_response = client.get(f"/api/messages/{msg_id}")
        assert get_response.status_code == 200


class TestDeleteMessage:
    """Tests for DELETE /api/messages/{message_id}"""

    def test_delete_existing_message(self):
        """Test deleting an existing message"""
        setup_test_messages()

        response = client.delete("/api/messages/msg_001")
        assert response.status_code == 204

        response = client.get("/api/messages/msg_001")
        assert response.status_code == 404

    def test_delete_nonexistent_message(self):
        """Test deleting a message that doesn't exist"""
        setup_test_messages()

        response = client.delete("/api/messages/nonexistent_message")
        assert response.status_code == 404

    def test_delete_reduces_message_count(self):
        """Test that deleting a message reduces total count"""
        setup_test_messages()

        response = client.get("/api/messages")
        initial_count = len(response.json())

        client.delete("/api/messages/msg_001")

        response = client.get("/api/messages")
        new_count = len(response.json())
        assert new_count == initial_count - 1

    def test_delete_idempotency(self):
        """Test that deleting the same message twice returns 404 second time"""
        setup_test_messages()

        response = client.delete("/api/messages/msg_001")
        assert response.status_code == 204

        response = client.delete("/api/messages/msg_001")
        assert response.status_code == 404

    def test_delete_does_not_affect_nodes(self):
        """Test that deleting a message doesn't delete nodes"""
        setup_test_messages()

        # Get the mesh_store from nodes router
        mesh_store = nodes_router.mesh_store

        client.delete("/api/messages/msg_001")

        node = mesh_store.get_node("node_001")
        assert node is not None


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_empty_messages_list(self):
        """Test GET /api/messages with no messages in store"""
        setup_test_nodes()

        response = client.get("/api/messages")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_message_with_same_sender_and_recipient(self):
        """Test creating a message where sender and recipient are the same"""
        setup_test_nodes()

        payload = {
            "sender_id": "node_001",
            "recipient_id": "node_001",
            "content": "Self message",
            "hops": 0,
        }

        response = client.post("/api/messages", json=payload)
        assert response.status_code == 201

    def test_concurrent_message_creation(self):
        """Test that multiple messages can be created concurrently"""
        setup_test_nodes()

        payload1 = {"sender_id": "node_001", "content": "Message 1", "hops": 0}
        payload2 = {"sender_id": "node_002", "content": "Message 2", "hops": 0}

        response1 = client.post("/api/messages", json=payload1)
        response2 = client.post("/api/messages", json=payload2)

        assert response1.status_code == 201
        assert response2.status_code == 201
