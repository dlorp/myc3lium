"""Tests for security hardening: error detail leaks and production safety."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Node
from app.routers import messages as messages_router
from app.routers import nodes as nodes_router
from app.services.mesh_store import MeshStore

client = TestClient(app)


class TestErrorDetailLeaks:
    """Verify that API error responses do not expose internal details."""

    def test_messages_send_generic_error_on_failure(self):
        """POST /api/messages/send returns generic 500 without exception details."""
        mock_reticulum = MagicMock()
        mock_reticulum.available = True
        mock_reticulum.send_message.side_effect = RuntimeError(
            "serial port /dev/ttyACM0 disconnected"
        )

        original = messages_router.reticulum
        messages_router.reticulum = mock_reticulum
        try:
            response = client.post(
                "/api/messages/send",
                json={
                    "destination_hash": "abcdef1234567890",
                    "content": "test message",
                },
            )

            assert response.status_code == 500
            detail = response.json()["detail"]
            assert "serial" not in detail.lower()
            assert "ttyACM0" not in detail
            assert detail == "Failed to send message"
        finally:
            messages_router.reticulum = original

    def test_messages_send_http_exception_not_swallowed(self):
        """HTTPException from send_message failure propagates as 400, not 500."""
        mock_reticulum = MagicMock()
        mock_reticulum.available = True
        mock_reticulum.send_message.return_value = False  # Triggers 400 path

        original = messages_router.reticulum
        messages_router.reticulum = mock_reticulum
        try:
            response = client.post(
                "/api/messages/send",
                json={
                    "destination_hash": "abcdef1234567890",
                    "content": "test message",
                },
            )

            assert response.status_code == 400
            assert response.json()["detail"] == "Failed to send message via Reticulum"
        finally:
            messages_router.reticulum = original

    def test_messages_create_generic_error_on_failure(self):
        """POST /api/messages returns generic 400 without leaking internal details."""
        with patch.object(
            MeshStore,
            "add_message",
            side_effect=ValueError("Message with ID msg_abc123 already exists"),
        ):
            response = client.post(
                "/api/messages",
                json={
                    "sender_id": "node_001",
                    "recipient_id": "node_002",
                    "content": "test message",
                },
            )

            assert response.status_code == 400
            detail = response.json()["detail"]
            assert "msg_abc123" not in detail
            assert detail == "Failed to create message"

    def test_nodes_create_duplicate_generic_error(self):
        """POST /api/nodes with duplicate ID returns generic 400 without echoing ID."""
        mesh_store = nodes_router.mesh_store
        mesh_store.clear()

        test_node = Node(
            id="dup_test_node",
            type="HYPHA",
            callsign="test-node",
            status="online",
            last_seen=datetime.now(timezone.utc),
        )
        mesh_store.add_node(test_node)

        response = client.post(
            "/api/nodes",
            json={
                "id": "dup_test_node",
                "type": "HYPHA",
                "callsign": "test-node-2",
                "status": "online",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        # Must not echo back the node ID
        assert "dup_test_node" not in detail
        assert detail == "Node with this ID already exists"


class TestIntelligenceObservationErrorLeak:
    """Test intelligence_api observation endpoint does not leak ValueError details."""

    def test_observation_bad_metadata_returns_generic_error(self):
        """POST /api/intelligence/observation returns generic 400 for bad metadata."""
        from intelligence_api import app as intel_app

        intel_client = TestClient(intel_app)

        with (
            patch(
                "intelligence_api.security.verify_api_token",
                return_value=True,
            ),
            patch(
                "intelligence_api.security.rate_limit",
                return_value=True,
            ),
            patch(
                "intelligence_api.security.validate_observation_metadata",
                side_effect=ValueError("Metadata too large: 2048 bytes (max 1KB)"),
            ),
        ):
            response = intel_client.post(
                "/api/intelligence/observation",
                params={"obs_type": "signal", "lat": "61.2", "lon": "-149.9"},
                json={"some": "metadata"},
                headers={"Authorization": "Bearer fake-token"},
            )

            assert response.status_code == 400
            detail = response.json()["detail"]
            assert "2048" not in detail
            assert "bytes" not in detail.lower()
            assert detail == "Invalid observation metadata"
