"""Integration tests for thread-message lifecycle flows"""

import time

from .helpers.api_helpers import (
    create_message,
    get_message,
    get_messages,
    verify_message_structure,
)


class TestThreadMessageLifecycle:
    """Test complete lifecycle: Thread → Messages → Verification"""

    def test_thread_exists_and_message_flow(self, client):
        """Test: Get thread, post messages, verify in GET

        Flow:
        1. Get existing nodes from mesh_store
        2. Post messages between nodes
        3. Verify messages appear in GET endpoints
        """
        # Get all nodes from mesh_store
        nodes_response = client.get("/api/nodes")
        assert nodes_response.status_code == 200
        nodes = nodes_response.json()
        assert len(nodes) >= 2, "Need at least 2 nodes for testing"

        # Use first two nodes
        source_id = nodes[0]["id"]
        target_id = nodes[1]["id"]

        # Post a message from source to target
        msg1 = create_message(
            client,
            sender_id=source_id,
            recipient_id=target_id,
            content="Test message via thread link",
        )
        verify_message_structure(msg1)

        # Verify message can be retrieved by ID
        retrieved = get_message(client, msg1["id"])
        assert retrieved is not None
        assert retrieved["id"] == msg1["id"]
        assert retrieved["content"] == "Test message via thread link"
        assert retrieved["sender_id"] == source_id
        assert retrieved["recipient_id"] == target_id

        # Verify message appears in GET /api/messages
        all_messages = get_messages(client)
        message_ids = [m["id"] for m in all_messages]
        assert msg1["id"] in message_ids

        # Post a reply message
        msg2 = create_message(
            client,
            sender_id=target_id,
            recipient_id=source_id,
            content="Reply message",
        )

        # Verify both messages exist
        messages = get_messages(client, limit=10)
        new_ids = [m["id"] for m in messages]
        assert msg1["id"] in new_ids
        assert msg2["id"] in new_ids

    def test_message_ordering(self, client):
        """Test: Post 3 messages, verify correct timestamp order

        Messages should be returned in newest-first order
        """
        # Get a valid node
        nodes_response = client.get("/api/nodes")
        assert nodes_response.status_code == 200
        nodes = nodes_response.json()
        assert len(nodes) >= 2, "Need at least 2 nodes for testing"

        sender = nodes[0]["id"]
        recipient = nodes[1]["id"]

        # Post 3 messages with small delays to ensure distinct timestamps
        messages = []
        for i in range(3):
            msg = create_message(
                client,
                sender_id=sender,
                recipient_id=recipient,
                content=f"Message {i + 1}",
            )
            messages.append(msg)
            time.sleep(0.01)  # Small delay to ensure timestamp difference

        # Get all messages
        all_messages = get_messages(client, limit=10)

        # Find our messages in the response
        our_messages = [m for m in all_messages if m["id"] in [msg["id"] for msg in messages]]
        assert len(our_messages) == 3, "All 3 messages should be returned"

        # Verify they're in newest-first order (msg3, msg2, msg1)
        assert our_messages[0]["content"] == "Message 3"
        assert our_messages[1]["content"] == "Message 2"
        assert our_messages[2]["content"] == "Message 1"

        # Verify timestamps are in descending order
        for i in range(len(our_messages) - 1):
            ts1 = our_messages[i]["timestamp"]
            ts2 = our_messages[i + 1]["timestamp"]
            assert ts1 >= ts2, "Messages should be ordered newest first"


class TestCrossEndpointConsistency:
    """Test consistency across different API endpoints"""

    def test_message_count_consistency(self, client):
        """Test: Create message, verify stats are updated

        Note: The current API doesn't expose thread.message_count directly.
        This test verifies that message counts are consistent across endpoints.
        """
        # Get initial message count
        initial_messages = get_messages(client)
        initial_count = len(initial_messages)

        # Get nodes
        nodes_response = client.get("/api/nodes")
        nodes = nodes_response.json()
        assert len(nodes) >= 2

        # Create a new message
        create_message(
            client,
            sender_id=nodes[0]["id"],
            recipient_id=nodes[1]["id"],
            content="Count test message",
        )

        # Get updated message count
        updated_messages = get_messages(client)
        updated_count = len(updated_messages)

        # Verify count increased by 1
        assert updated_count == initial_count + 1

        # Verify via system stats endpoint (if available)
        stats_response = client.get("/api/system/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            assert stats["message_count"] == updated_count


class TestErrorPropagation:
    """Test error handling and validation across endpoints"""

    def test_bad_thread_id_returns_404(self, client):
        """Test: Bad thread ID in thread endpoint → 404"""
        response = client.get("/api/threads/nonexistent_thread_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_bad_message_id_returns_404(self, client):
        """Test: Bad message ID in message endpoint → 404"""
        response = client.get("/api/messages/nonexistent_message_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_sender_node(self, client):
        """Test: Message with nonexistent sender → 400 error"""
        response = client.post(
            "/api/messages",
            json={
                "sender_id": "nonexistent_node",
                "recipient_id": None,
                "content": "Test message",
                "hops": 0,
            },
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    def test_invalid_recipient_node(self, client):
        """Test: Message with nonexistent recipient → 400 error"""
        # Get a valid sender
        nodes_response = client.get("/api/nodes")
        nodes = nodes_response.json()
        assert len(nodes) > 0

        response = client.post(
            "/api/messages",
            json={
                "sender_id": nodes[0]["id"],
                "recipient_id": "nonexistent_recipient",
                "content": "Test message",
                "hops": 0,
            },
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()

    def test_broadcast_message_succeeds(self, client):
        """Test: Broadcast message (recipient_id=None) succeeds"""
        nodes_response = client.get("/api/nodes")
        nodes = nodes_response.json()
        assert len(nodes) > 0

        msg = create_message(
            client,
            sender_id=nodes[0]["id"],
            recipient_id=None,
            content="Broadcast test",
        )

        assert msg["recipient_id"] is None
        assert msg["content"] == "Broadcast test"


class TestThreadDeletion:
    """Test thread deletion and cascading behavior"""

    def test_thread_deletion_api(self, client):
        """Test: Delete thread via API

        Note: Thread deletion doesn't cascade to messages in current implementation.
        This is a known limitation to document.
        """
        # Get a thread to delete
        threads_response = client.get("/api/threads")
        threads = threads_response.json()
        assert len(threads) > 0

        thread_to_delete = threads[0]
        thread_id = thread_to_delete["id"]

        # Delete the thread
        delete_response = client.delete(f"/api/threads/{thread_id}")
        assert delete_response.status_code == 204

        # Verify thread is gone
        get_response = client.get(f"/api/threads/{thread_id}")
        assert get_response.status_code == 404

        # Verify thread count decreased
        remaining_threads = client.get("/api/threads").json()
        assert len(remaining_threads) == len(threads) - 1


class TestFilteringAndPagination:
    """Test message filtering and pagination"""

    def test_filter_messages_by_sender(self, client):
        """Test: Filter messages by sender_id"""
        nodes_response = client.get("/api/nodes")
        nodes = nodes_response.json()
        assert len(nodes) >= 2

        sender = nodes[0]["id"]
        recipient = nodes[1]["id"]

        # Create a message
        msg = create_message(
            client,
            sender_id=sender,
            recipient_id=recipient,
            content="Filter test message",
        )

        # Get messages filtered by sender
        filtered = get_messages(client, sender_id=sender)

        # Verify our message is in the results
        message_ids = [m["id"] for m in filtered]
        assert msg["id"] in message_ids

        # Verify all messages are from the sender
        for message in filtered:
            assert message["sender_id"] == sender

    def test_filter_messages_by_recipient(self, client):
        """Test: Filter messages by recipient_id"""
        nodes_response = client.get("/api/nodes")
        nodes = nodes_response.json()
        assert len(nodes) >= 2

        sender = nodes[0]["id"]
        recipient = nodes[1]["id"]

        # Create a message
        msg = create_message(
            client,
            sender_id=sender,
            recipient_id=recipient,
            content="Recipient filter test",
        )

        # Get messages filtered by recipient
        filtered = get_messages(client, recipient_id=recipient)

        # Verify our message is in the results
        message_ids = [m["id"] for m in filtered]
        assert msg["id"] in message_ids

        # Verify all messages are to the recipient
        for message in filtered:
            assert message["recipient_id"] == recipient

    def test_message_limit(self, client):
        """Test: Message limit parameter works"""
        # Get messages with limit=5
        messages = get_messages(client, limit=5)

        # Should return at most 5 messages
        assert len(messages) <= 5
