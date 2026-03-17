"""Comprehensive tests for thread management endpoints"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGetThreads:
    """Tests for GET /api/threads"""

    def test_get_all_threads(self):
        """Test retrieving all threads without filters"""
        response = client.get("/api/threads")
        assert response.status_code == 200

        threads = response.json()
        assert isinstance(threads, list)
        assert len(threads) > 0

        # Validate thread structure
        thread = threads[0]
        assert "id" in thread
        assert "source_id" in thread
        assert "target_id" in thread
        assert "radio_type" in thread
        assert "quality" in thread
        assert "established" in thread

    def test_filter_by_node_id_source(self):
        """Test filtering threads by source node ID"""
        response = client.get("/api/threads?node_id=node_001")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["source_id"] == "node_001" or thread["target_id"] == "node_001"

    def test_filter_by_node_id_target(self):
        """Test filtering threads by target node ID"""
        response = client.get("/api/threads?node_id=node_002")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["source_id"] == "node_002" or thread["target_id"] == "node_002"

    def test_filter_by_radio_type_lora(self):
        """Test filtering threads by LoRa radio type"""
        response = client.get("/api/threads?radio_type=LoRa")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["radio_type"] == "LoRa"

    def test_filter_by_radio_type_halow(self):
        """Test filtering threads by HaLow radio type"""
        response = client.get("/api/threads?radio_type=HaLow")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["radio_type"] == "HaLow"

    def test_filter_by_radio_type_wifi(self):
        """Test filtering threads by WiFi radio type"""
        response = client.get("/api/threads?radio_type=WiFi")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["radio_type"] == "WiFi"

    def test_filter_by_min_quality_low(self):
        """Test filtering threads by minimum quality (0.5)"""
        response = client.get("/api/threads?min_quality=0.5")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["quality"] >= 0.5

    def test_filter_by_min_quality_high(self):
        """Test filtering threads by high minimum quality (0.9)"""
        response = client.get("/api/threads?min_quality=0.9")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["quality"] >= 0.9

    def test_filter_by_min_quality_zero(self):
        """Test filtering threads with min_quality=0 (should return all)"""
        response = client.get("/api/threads?min_quality=0.0")
        assert response.status_code == 200

        threads = response.json()
        assert len(threads) > 0

    def test_filter_by_node_and_radio_type(self):
        """Test combining node_id and radio_type filters"""
        response = client.get("/api/threads?node_id=node_001&radio_type=LoRa")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["source_id"] == "node_001" or thread["target_id"] == "node_001"
            assert thread["radio_type"] == "LoRa"

    def test_filter_by_node_and_min_quality(self):
        """Test combining node_id and min_quality filters"""
        response = client.get("/api/threads?node_id=node_001&min_quality=0.7")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["source_id"] == "node_001" or thread["target_id"] == "node_001"
            assert thread["quality"] >= 0.7

    def test_filter_by_all_parameters(self):
        """Test combining all three filters"""
        response = client.get("/api/threads?node_id=node_001&radio_type=LoRa&min_quality=0.5")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["source_id"] == "node_001" or thread["target_id"] == "node_001"
            assert thread["radio_type"] == "LoRa"
            assert thread["quality"] >= 0.5

    def test_empty_filter_result(self):
        """Test that empty results are valid when filters match nothing"""
        response = client.get("/api/threads?min_quality=0.999")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_thread_field_types(self):
        """Test that all thread fields have correct types"""
        response = client.get("/api/threads")
        threads = response.json()

        thread = threads[0]
        assert isinstance(thread["id"], str)
        assert isinstance(thread["source_id"], str)
        assert isinstance(thread["target_id"], str)
        assert thread["radio_type"] in ["LoRa", "HaLow", "WiFi"]
        assert isinstance(thread["quality"], (int, float))
        assert 0.0 <= thread["quality"] <= 1.0
        assert isinstance(thread["established"], str)  # ISO datetime string

        # Optional fields
        if thread.get("rssi") is not None:
            assert isinstance(thread["rssi"], int)
        if thread.get("latency") is not None:
            assert isinstance(thread["latency"], int)


class TestGetThreadById:
    """Tests for GET /api/threads/{thread_id}"""

    def test_get_existing_thread(self):
        """Test retrieving a specific thread by ID"""
        # Get all threads to get a valid ID
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Get specific thread
        response = client.get(f"/api/threads/{thread_id}")
        assert response.status_code == 200

        thread = response.json()
        assert thread["id"] == thread_id

    def test_get_nonexistent_thread(self):
        """Test retrieving a thread that doesn't exist"""
        response = client.get("/api/threads/nonexistent_thread_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_each_thread(self):
        """Test that each thread can be retrieved individually"""
        response = client.get("/api/threads")
        threads = response.json()

        for thread in threads:
            thread_id = thread["id"]
            response = client.get(f"/api/threads/{thread_id}")
            assert response.status_code == 200
            retrieved_thread = response.json()
            assert retrieved_thread["id"] == thread_id


class TestPatchThread:
    """Tests for PATCH /api/threads/{thread_id}"""

    def test_update_thread_quality(self):
        """Test updating a thread's quality"""
        # Get a valid thread
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Update quality
        new_quality = 0.75
        response = client.patch(f"/api/threads/{thread_id}", json={"quality": new_quality})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["id"] == thread_id
        assert updated_thread["quality"] == new_quality

    def test_update_thread_latency(self):
        """Test updating a thread's latency"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"latency": 50})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["latency"] == 50

    def test_update_thread_rssi(self):
        """Test updating a thread's RSSI"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"rssi": -65})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["rssi"] == -65

    def test_update_multiple_fields(self):
        """Test updating multiple thread fields at once"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        update_data = {"quality": 0.88, "latency": 35, "rssi": -70}
        response = client.patch(f"/api/threads/{thread_id}", json=update_data)
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["quality"] == 0.88
        assert updated_thread["latency"] == 35
        assert updated_thread["rssi"] == -70

    def test_update_quality_to_minimum(self):
        """Test updating quality to minimum value (0.0)"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"quality": 0.0})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["quality"] == 0.0

    def test_update_quality_to_maximum(self):
        """Test updating quality to maximum value (1.0)"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"quality": 1.0})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["quality"] == 1.0

    def test_patch_empty_body(self):
        """Test PATCH with no fields updates timestamp"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]
        original_established = threads[0]["established"]

        response = client.patch(f"/api/threads/{thread_id}", json={})
        assert response.status_code == 200

        updated_thread = response.json()
        # Established timestamp should be updated even with empty patch
        assert updated_thread["established"] != original_established

    def test_patch_nonexistent_thread(self):
        """Test PATCH on a thread that doesn't exist"""
        response = client.patch("/api/threads/nonexistent_thread", json={"quality": 0.9})
        assert response.status_code == 404

    def test_patch_preserves_other_fields(self):
        """Test that PATCH only updates specified fields"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]
        original_source = threads[0]["source_id"]
        original_target = threads[0]["target_id"]
        original_radio = threads[0]["radio_type"]

        # Update only quality
        response = client.patch(f"/api/threads/{thread_id}", json={"quality": 0.65})
        updated_thread = response.json()

        # Other fields should remain unchanged
        assert updated_thread["source_id"] == original_source
        assert updated_thread["target_id"] == original_target
        assert updated_thread["radio_type"] == original_radio

    def test_patch_with_null_values(self):
        """Test PATCH with null values for optional fields"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Set optional fields to null
        response = client.patch(f"/api/threads/{thread_id}", json={"rssi": None, "latency": None})
        assert response.status_code == 200

        updated_thread = response.json()
        assert updated_thread["rssi"] is None
        assert updated_thread["latency"] is None


class TestDeleteThread:
    """Tests for DELETE /api/threads/{thread_id}"""

    def test_delete_existing_thread(self):
        """Test deleting an existing thread"""
        # Get all threads
        response = client.get("/api/threads")
        threads_before = response.json()
        thread_to_delete = threads_before[0]["id"]

        # Delete the thread
        response = client.delete(f"/api/threads/{thread_to_delete}")
        assert response.status_code == 204
        assert response.content == b""

        # Verify thread is gone
        response = client.get(f"/api/threads/{thread_to_delete}")
        assert response.status_code == 404

        # Verify thread count decreased
        response = client.get("/api/threads")
        threads_after = response.json()
        assert len(threads_after) == len(threads_before) - 1

    def test_delete_nonexistent_thread(self):
        """Test deleting a thread that doesn't exist"""
        response = client.delete("/api/threads/nonexistent_thread")
        assert response.status_code == 404

    def test_delete_multiple_threads(self):
        """Test deleting multiple threads sequentially"""
        response = client.get("/api/threads")
        threads = response.json()
        initial_count = len(threads)

        # Delete first two threads
        for i in range(2):
            thread_id = threads[i]["id"]
            response = client.delete(f"/api/threads/{thread_id}")
            assert response.status_code == 204

        # Verify count decreased
        response = client.get("/api/threads")
        remaining_threads = response.json()
        assert len(remaining_threads) == initial_count - 2

    def test_delete_idempotency(self):
        """Test that deleting the same thread twice returns 404 second time"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # First delete succeeds
        response = client.delete(f"/api/threads/{thread_id}")
        assert response.status_code == 204

        # Second delete fails
        response = client.delete(f"/api/threads/{thread_id}")
        assert response.status_code == 404

    def test_delete_by_node_filter(self):
        """Test deleting all threads for a specific node"""
        # Get threads for a node
        response = client.get("/api/threads?node_id=node_003")
        threads_to_delete = response.json()

        # Delete each thread
        for thread in threads_to_delete:
            response = client.delete(f"/api/threads/{thread['id']}")
            assert response.status_code == 204

        # Verify no threads remain for this node
        response = client.get("/api/threads?node_id=node_003")
        remaining_threads = response.json()
        assert len(remaining_threads) == 0


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_invalid_radio_type_filter(self):
        """Test that invalid radio type filter is rejected"""
        response = client.get("/api/threads?radio_type=INVALID_TYPE")
        assert response.status_code == 422  # Validation error

    def test_invalid_min_quality_negative(self):
        """Test that negative min_quality is rejected"""
        response = client.get("/api/threads?min_quality=-0.5")
        assert response.status_code == 422  # Validation error

    def test_invalid_min_quality_too_high(self):
        """Test that min_quality > 1.0 is rejected"""
        response = client.get("/api/threads?min_quality=1.5")
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_quality_negative(self):
        """Test PATCH with negative quality value"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"quality": -0.1})
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_quality_too_high(self):
        """Test PATCH with quality value > 1.0"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        response = client.patch(f"/api/threads/{thread_id}", json={"quality": 1.5})
        assert response.status_code == 422  # Validation error

    def test_patch_with_invalid_field(self):
        """Test PATCH with non-updatable field (should be ignored)"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]
        original_source = threads[0]["source_id"]

        # Try to update source_id (not in ThreadPatch schema)
        response = client.patch(f"/api/threads/{thread_id}", json={"source_id": "node_999"})
        assert response.status_code == 200

        updated_thread = response.json()
        # Source ID should remain unchanged (field ignored)
        assert updated_thread["source_id"] == original_source

    def test_concurrent_operations(self):
        """Test that operations maintain consistency"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Multiple updates
        client.patch(f"/api/threads/{thread_id}", json={"quality": 0.9})
        client.patch(f"/api/threads/{thread_id}", json={"latency": 25})

        # Verify final state
        response = client.get(f"/api/threads/{thread_id}")
        thread = response.json()
        assert thread["quality"] == 0.9
        assert thread["latency"] == 25

    def test_filter_nonexistent_node(self):
        """Test filtering by a node that has no threads"""
        response = client.get("/api/threads?node_id=nonexistent_node")
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 0

    def test_quality_precision(self):
        """Test that quality values maintain precision"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Update with precise quality value
        response = client.patch(f"/api/threads/{thread_id}", json={"quality": 0.8765})
        assert response.status_code == 200

        updated_thread = response.json()
        assert abs(updated_thread["quality"] - 0.8765) < 0.0001


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios"""

    def test_find_low_quality_threads(self):
        """Test finding threads that need attention (low quality)"""
        response = client.get("/api/threads?min_quality=0.0")
        all_threads = response.json()

        low_quality_threads = [t for t in all_threads if t["quality"] < 0.5]

        # Should be able to identify low quality threads
        assert isinstance(low_quality_threads, list)

    def test_upgrade_thread_metrics(self):
        """Test upgrading a thread's quality and latency"""
        response = client.get("/api/threads")
        threads = response.json()
        thread_id = threads[0]["id"]

        # Simulate network improvement
        improvements = {"quality": 0.95, "latency": 10, "rssi": -45}
        response = client.patch(f"/api/threads/{thread_id}", json=improvements)
        assert response.status_code == 200

        improved_thread = response.json()
        assert improved_thread["quality"] == 0.95
        assert improved_thread["latency"] == 10
        assert improved_thread["rssi"] == -45

    def test_monitor_node_connectivity(self):
        """Test monitoring all connections for a specific node"""
        node_id = "node_001"

        # Get all threads for node
        response = client.get(f"/api/threads?node_id={node_id}")
        assert response.status_code == 200

        threads = response.json()
        # Verify all threads involve the specified node
        for thread in threads:
            assert thread["source_id"] == node_id or thread["target_id"] == node_id

    def test_filter_by_technology_and_quality(self):
        """Test finding high-quality connections of a specific radio type"""
        response = client.get("/api/threads?radio_type=LoRa&min_quality=0.8")
        assert response.status_code == 200

        threads = response.json()
        for thread in threads:
            assert thread["radio_type"] == "LoRa"
            assert thread["quality"] >= 0.8
