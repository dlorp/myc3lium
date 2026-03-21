"""Comprehensive tests for node management endpoints"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGetNodes:
    """Tests for GET /api/nodes"""

    def test_get_all_nodes(self):
        """Test retrieving all nodes without filters"""
        response = client.get("/api/nodes")
        assert response.status_code == 200

        nodes = response.json()
        assert isinstance(nodes, list)
        assert len(nodes) > 0

        # Validate node structure
        node = nodes[0]
        assert "id" in node
        assert "type" in node
        assert "callsign" in node
        assert "status" in node
        assert "last_seen" in node

    def test_filter_by_status_online(self):
        """Test filtering nodes by online status"""
        response = client.get("/api/nodes?status=online")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["status"] == "online"

    def test_filter_by_status_offline(self):
        """Test filtering nodes by offline status"""
        response = client.get("/api/nodes?status=offline")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["status"] == "offline"

    def test_filter_by_status_degraded(self):
        """Test filtering nodes by degraded status"""
        response = client.get("/api/nodes?status=degraded")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["status"] == "degraded"

    def test_filter_by_type_spore(self):
        """Test filtering nodes by SPORE type"""
        response = client.get("/api/nodes?type=SPORE")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["type"] == "SPORE"

    def test_filter_by_type_hypha(self):
        """Test filtering nodes by HYPHA type"""
        response = client.get("/api/nodes?type=HYPHA")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["type"] == "HYPHA"

    def test_filter_by_type_frond(self):
        """Test filtering nodes by FROND type"""
        response = client.get("/api/nodes?type=FROND")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["type"] == "FROND"

    def test_filter_by_type_rhizome(self):
        """Test filtering nodes by RHIZOME type"""
        response = client.get("/api/nodes?type=RHIZOME")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["type"] == "RHIZOME"

    def test_filter_by_status_and_type(self):
        """Test combining status and type filters"""
        response = client.get("/api/nodes?status=online&type=HYPHA")
        assert response.status_code == 200

        nodes = response.json()
        for node in nodes:
            assert node["status"] == "online"
            assert node["type"] == "HYPHA"

    def test_empty_filter_result(self):
        """Test that empty results are valid when filters match nothing"""
        # This might return empty if no nodes match
        response = client.get("/api/nodes?status=offline&type=SPORE")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_node_field_types(self):
        """Test that all node fields have correct types"""
        response = client.get("/api/nodes")
        nodes = response.json()

        node = nodes[0]
        assert isinstance(node["id"], str)
        assert node["type"] in ["SPORE", "HYPHA", "FROND", "RHIZOME"]
        assert isinstance(node["callsign"], str)
        assert node["status"] in ["online", "offline", "degraded"]
        assert isinstance(node["last_seen"], str)  # ISO datetime string

        # Optional fields
        if node.get("rssi") is not None:
            assert isinstance(node["rssi"], int)
        if node.get("battery") is not None:
            assert isinstance(node["battery"], int)
            assert 0 <= node["battery"] <= 100
        if node.get("position") is not None:
            assert isinstance(node["position"], dict)
            assert "lat" in node["position"]
            assert "lon" in node["position"]


class TestGetNodeById:
    """Tests for GET /api/nodes/{node_id}"""

    def test_get_existing_node(self):
        """Test retrieving a specific node by ID"""
        # Get all nodes to get a valid ID
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        # Get specific node
        response = client.get(f"/api/nodes/{node_id}")
        assert response.status_code == 200

        node = response.json()
        assert node["id"] == node_id

    def test_get_nonexistent_node(self):
        """Test retrieving a node that doesn't exist"""
        response = client.get("/api/nodes/nonexistent_node_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_each_node(self):
        """Test that each node can be retrieved individually"""
        response = client.get("/api/nodes")
        nodes = response.json()

        for node in nodes:
            node_id = node["id"]
            response = client.get(f"/api/nodes/{node_id}")
            assert response.status_code == 200
            retrieved_node = response.json()
            assert retrieved_node["id"] == node_id


class TestPatchNode:
    """Tests for PATCH /api/nodes/{node_id}"""

    def test_update_node_status(self):
        """Test updating a node's status"""
        # Get a valid node
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]
        original_status = nodes[0]["status"]

        # Update status
        new_status = "degraded" if original_status != "degraded" else "online"
        response = client.patch(f"/api/nodes/{node_id}", json={"status": new_status})
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["id"] == node_id
        assert updated_node["status"] == new_status

    def test_update_node_callsign(self):
        """Test updating a node's callsign"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(
            f"/api/nodes/{node_id}", json={"callsign": "new-callsign"}
        )
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["callsign"] == "new-callsign"

    def test_update_node_type(self):
        """Test updating a node's type"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(f"/api/nodes/{node_id}", json={"type": "RHIZOME"})
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["type"] == "RHIZOME"

    def test_update_node_rssi(self):
        """Test updating a node's RSSI"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(f"/api/nodes/{node_id}", json={"rssi": -75})
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["rssi"] == -75

    def test_update_node_battery(self):
        """Test updating a node's battery level"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(f"/api/nodes/{node_id}", json={"battery": 42})
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["battery"] == 42

    def test_update_node_position(self):
        """Test updating a node's position"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        new_position = {"lat": 45.5231, "lon": -122.6765}
        response = client.patch(
            f"/api/nodes/{node_id}", json={"position": new_position}
        )
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["position"] == new_position

    def test_update_multiple_fields(self):
        """Test updating multiple node fields at once"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        update_data = {"status": "online", "battery": 95, "rssi": -60}
        response = client.patch(f"/api/nodes/{node_id}", json=update_data)
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["status"] == "online"
        assert updated_node["battery"] == 95
        assert updated_node["rssi"] == -60

    def test_patch_empty_body(self):
        """Test PATCH with no fields updates timestamp"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]
        original_last_seen = nodes[0]["last_seen"]

        response = client.patch(f"/api/nodes/{node_id}", json={})
        assert response.status_code == 200

        updated_node = response.json()
        # Last seen should be updated even with empty patch
        assert updated_node["last_seen"] != original_last_seen

    def test_patch_nonexistent_node(self):
        """Test PATCH on a node that doesn't exist"""
        response = client.patch(
            "/api/nodes/nonexistent_node", json={"status": "online"}
        )
        assert response.status_code == 404

    def test_patch_preserves_other_fields(self):
        """Test that PATCH only updates specified fields"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]
        original_type = nodes[0]["type"]
        original_callsign = nodes[0]["callsign"]

        # Update only status
        response = client.patch(f"/api/nodes/{node_id}", json={"status": "degraded"})
        updated_node = response.json()

        # Other fields should remain unchanged
        assert updated_node["type"] == original_type
        assert updated_node["callsign"] == original_callsign


class TestDeleteNode:
    """Tests for DELETE /api/nodes/{node_id}"""

    def test_delete_existing_node(self):
        """Test deleting an existing node"""
        # Get all nodes
        response = client.get("/api/nodes")
        nodes_before = response.json()
        node_to_delete = nodes_before[0]["id"]

        # Delete the node
        response = client.delete(f"/api/nodes/{node_to_delete}")
        assert response.status_code == 204
        assert response.content == b""

        # Verify node is gone
        response = client.get(f"/api/nodes/{node_to_delete}")
        assert response.status_code == 404

        # Verify node count decreased
        response = client.get("/api/nodes")
        nodes_after = response.json()
        assert len(nodes_after) == len(nodes_before) - 1

    def test_delete_nonexistent_node(self):
        """Test deleting a node that doesn't exist"""
        response = client.delete("/api/nodes/nonexistent_node")
        assert response.status_code == 404

    def test_delete_multiple_nodes(self):
        """Test deleting multiple nodes sequentially"""
        response = client.get("/api/nodes")
        nodes = response.json()
        initial_count = len(nodes)

        # Delete first two nodes
        for i in range(2):
            node_id = nodes[i]["id"]
            response = client.delete(f"/api/nodes/{node_id}")
            assert response.status_code == 204

        # Verify count decreased
        response = client.get("/api/nodes")
        remaining_nodes = response.json()
        assert len(remaining_nodes) == initial_count - 2

    def test_delete_idempotency(self):
        """Test that deleting the same node twice returns 404 second time"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        # First delete succeeds
        response = client.delete(f"/api/nodes/{node_id}")
        assert response.status_code == 204

        # Second delete fails
        response = client.delete(f"/api/nodes/{node_id}")
        assert response.status_code == 404


class TestUpdateNodeStatus:
    """Tests for POST /api/nodes/{node_id}/status (legacy endpoint)"""

    def test_update_status_to_online(self):
        """Test updating status to online"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.post(f"/api/nodes/{node_id}/status?status=online")
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["status"] == "online"

    def test_update_status_to_offline(self):
        """Test updating status to offline"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.post(f"/api/nodes/{node_id}/status?status=offline")
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["status"] == "offline"

    def test_update_status_to_degraded(self):
        """Test updating status to degraded"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.post(f"/api/nodes/{node_id}/status?status=degraded")
        assert response.status_code == 200

        updated_node = response.json()
        assert updated_node["status"] == "degraded"

    def test_update_status_invalid(self):
        """Test updating to an invalid status"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.post(f"/api/nodes/{node_id}/status?status=invalid_status")
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_update_status_nonexistent_node(self):
        """Test updating status of nonexistent node"""
        response = client.post("/api/nodes/nonexistent_node/status?status=online")
        assert response.status_code == 404

    def test_update_status_updates_timestamp(self):
        """Test that updating status updates last_seen timestamp"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]
        original_last_seen = nodes[0]["last_seen"]

        response = client.post(f"/api/nodes/{node_id}/status?status=online")
        updated_node = response.json()

        # Timestamp should be updated
        assert updated_node["last_seen"] != original_last_seen


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_invalid_status_filter(self):
        """Test that invalid status filter is ignored gracefully"""
        # FastAPI should validate and reject invalid enum values
        response = client.get("/api/nodes?status=invalid_status")
        assert response.status_code == 422  # Validation error

    def test_invalid_type_filter(self):
        """Test that invalid type filter is rejected"""
        response = client.get("/api/nodes?type=INVALID_TYPE")
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_type(self):
        """Test PATCH with invalid node type"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(f"/api/nodes/{node_id}", json={"type": "INVALID_TYPE"})
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_status(self):
        """Test PATCH with invalid status"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        response = client.patch(
            f"/api/nodes/{node_id}", json={"status": "invalid_status"}
        )
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_battery(self):
        """Test PATCH with battery value out of range"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        # Battery should be 0-100
        response = client.patch(f"/api/nodes/{node_id}", json={"battery": 150})
        assert response.status_code == 422  # Validation error

    def test_concurrent_operations(self):
        """Test that operations maintain consistency"""
        response = client.get("/api/nodes")
        nodes = response.json()
        node_id = nodes[0]["id"]

        # Multiple updates
        client.patch(f"/api/nodes/{node_id}", json={"status": "online"})
        client.patch(f"/api/nodes/{node_id}", json={"battery": 50})

        # Verify final state
        response = client.get(f"/api/nodes/{node_id}")
        node = response.json()
        assert node["status"] == "online"
        assert node["battery"] == 50
