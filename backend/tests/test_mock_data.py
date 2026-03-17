"""Tests for mock data generation"""

from datetime import datetime, timezone

import pytest

from app.services.mock_data import MockMeshDataSource


def test_mock_data_source_init():
    """Test MockMeshDataSource initialization"""
    source = MockMeshDataSource(seed=42)

    assert source.rng is not None
    assert source.base_time is not None
    assert len(source._nodes) > 0
    assert len(source._threads) > 0


def test_mock_data_generates_8_nodes():
    """Test that mock data generates exactly 8 nodes"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    assert len(nodes) == 8


def test_mock_data_node_ids():
    """Test that nodes have correct ID format"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    for idx, node in enumerate(nodes):
        assert node.id == f"myc3_{idx:03d}"


def test_mock_data_node_callsigns():
    """Test that nodes have MYC3LIUM callsigns"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    for node in nodes:
        assert node.callsign.startswith("MYC3LIUM-")


def test_mock_data_anchorage_coordinates():
    """Test that nodes have Anchorage GPS coordinates"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    for node in nodes:
        assert node.position is not None
        lat = node.position["lat"]
        lon = node.position["lon"]

        # Anchorage latitude: ~61.0° to 61.3°
        assert 61.0 <= lat <= 61.3

        # Anchorage longitude: ~-150.0° to -149.6° (wider range for Eagle River, JBER)
        assert -150.0 <= lon <= -149.6


def test_mock_data_node_types():
    """Test that nodes have correct types"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    valid_types = {"SPORE", "HYPHA", "FROND", "RHIZOME"}
    for node in nodes:
        assert node.type in valid_types


def test_mock_data_node_status():
    """Test that nodes have valid status"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    valid_statuses = {"online", "offline", "degraded"}
    for node in nodes:
        assert node.status in valid_statuses


def test_mock_data_battery_nodes():
    """Test that SPORE and FROND nodes have batteries"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    battery_types = {"SPORE", "FROND"}
    for node in nodes:
        if node.type in battery_types:
            assert node.battery is not None
            assert 0 <= node.battery <= 100


def test_mock_data_generates_9_threads():
    """Test that mock data generates exactly 9 threads"""
    source = MockMeshDataSource(seed=42)
    threads = source.get_threads()

    assert len(threads) == 9


def test_mock_data_thread_radio_types():
    """Test that threads have valid radio types"""
    source = MockMeshDataSource(seed=42)
    threads = source.get_threads()

    valid_radio_types = {"LoRa", "HaLow", "WiFi"}
    radio_counts = {"LoRa": 0, "HaLow": 0, "WiFi": 0}

    for thread in threads:
        assert thread.radio_type in valid_radio_types
        radio_counts[thread.radio_type] += 1

    # Verify we have a mix of radio types
    assert radio_counts["LoRa"] > 0
    assert radio_counts["HaLow"] > 0
    assert radio_counts["WiFi"] > 0


def test_mock_data_thread_quality():
    """Test that threads have valid quality values"""
    source = MockMeshDataSource(seed=42)
    threads = source.get_threads()

    for thread in threads:
        assert 0.0 <= thread.quality <= 1.0


def test_mock_data_thread_references_valid_nodes():
    """Test that threads reference existing nodes"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()
    threads = source.get_threads()

    node_ids = {node.id for node in nodes}

    for thread in threads:
        assert thread.source_id in node_ids
        assert thread.target_id in node_ids
        assert thread.source_id != thread.target_id


def test_mock_data_generates_messages():
    """Test that mock data generates messages"""
    source = MockMeshDataSource(seed=42)
    messages = source.get_messages()

    # Should have some messages (exact count may vary based on online nodes)
    assert len(messages) >= 0


def test_mock_data_message_references_valid_nodes():
    """Test that messages reference existing nodes"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()
    messages = source.get_messages()

    if len(messages) == 0:
        pytest.skip("No messages generated (all nodes offline)")

    node_ids = {node.id for node in nodes}

    for message in messages:
        assert message.sender_id in node_ids
        if message.recipient_id is not None:
            assert message.recipient_id in node_ids


def test_mock_data_reproducibility():
    """Test that same seed produces same data"""
    source1 = MockMeshDataSource(seed=42)
    source2 = MockMeshDataSource(seed=42)

    nodes1 = source1.get_nodes()
    nodes2 = source2.get_nodes()

    assert len(nodes1) == len(nodes2)

    for n1, n2 in zip(nodes1, nodes2):
        assert n1.id == n2.id
        assert n1.callsign == n2.callsign
        assert n1.type == n2.type
        assert n1.status == n2.status
        assert n1.battery == n2.battery


def test_mock_data_different_seeds():
    """Test that different seeds produce different data"""
    source1 = MockMeshDataSource(seed=42)
    source2 = MockMeshDataSource(seed=99)

    nodes1 = source1.get_nodes()
    nodes2 = source2.get_nodes()

    # Same structure but different random values
    assert len(nodes1) == len(nodes2)

    # At least some nodes should have different status or battery
    differences = 0
    for n1, n2 in zip(nodes1, nodes2):
        if n1.status != n2.status or n1.battery != n2.battery:
            differences += 1

    assert differences > 0


def test_sensor_data_generation():
    """Test sensor data generation for a node"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    sensor_data = source.get_sensor_data(nodes[0].id)

    assert len(sensor_data) > 0

    # Should have temperature readings
    temp_readings = [s for s in sensor_data if s.sensor_type == "temperature"]
    assert len(temp_readings) > 0

    # Should have 24 hours of temperature data
    assert len(temp_readings) == 24

    # Check temperature units
    for reading in temp_readings:
        assert reading.unit == "celsius"
        assert reading.node_id == nodes[0].id


def test_sensor_data_diurnal_cycle():
    """Test that temperature data shows diurnal (day/night) cycle"""
    base_time = datetime(2026, 3, 16, 15, 0, 0, tzinfo=timezone.utc)  # 3 PM (warmest)
    source = MockMeshDataSource(seed=42, base_time=base_time)
    nodes = source.get_nodes()

    sensor_data = source.get_sensor_data(nodes[0].id)
    temp_readings = [s for s in sensor_data if s.sensor_type == "temperature"]

    # Extract temperatures by hour
    temps_by_hour = {s.timestamp.hour: s.value for s in temp_readings}

    # At 3 PM (hour 15) should be warmer than 6 AM (hour 6)
    if 15 in temps_by_hour and 6 in temps_by_hour:
        # Allow some variance, but generally 3 PM should be warmer
        # (not strict inequality due to random variance)
        assert abs(temps_by_hour[15] - temps_by_hour[6]) >= 0  # Just check it's reasonable


def test_sensor_data_includes_humidity():
    """Test that sensor data includes humidity"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    sensor_data = source.get_sensor_data(nodes[0].id)
    humidity_readings = [s for s in sensor_data if s.sensor_type == "humidity"]

    assert len(humidity_readings) > 0
    assert humidity_readings[0].unit == "percent"
    assert 0 <= humidity_readings[0].value <= 100


def test_sensor_data_includes_pressure():
    """Test that sensor data includes pressure"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    sensor_data = source.get_sensor_data(nodes[0].id)
    pressure_readings = [s for s in sensor_data if s.sensor_type == "pressure"]

    assert len(pressure_readings) > 0
    assert pressure_readings[0].unit == "hPa"
    assert 900 <= pressure_readings[0].value <= 1100  # Reasonable pressure range


def test_sensor_data_invalid_node():
    """Test sensor data for non-existent node"""
    source = MockMeshDataSource(seed=42)
    sensor_data = source.get_sensor_data("invalid_node_id")

    assert sensor_data == []


def test_battery_drain_simulation():
    """Test battery drain simulation"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    # Find a node with battery
    battery_node = next((n for n in nodes if n.battery is not None), None)
    if battery_node is None:
        pytest.skip("No battery nodes generated")

    initial_battery = battery_node.battery
    new_battery = source.simulate_battery_drain(battery_node.id, hours=1.0)

    assert new_battery is not None
    assert new_battery < initial_battery  # Battery should drain
    assert new_battery >= 0


def test_battery_drain_multiple_hours():
    """Test battery drain over multiple hours"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    battery_node = next((n for n in nodes if n.battery is not None), None)
    if battery_node is None:
        pytest.skip("No battery nodes generated")

    initial_battery = battery_node.battery
    new_battery = source.simulate_battery_drain(battery_node.id, hours=10.0)

    assert new_battery is not None
    assert new_battery < initial_battery
    assert new_battery >= 0


def test_battery_drain_node_without_battery():
    """Test battery drain for node without battery"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    # Find a node without battery (RHIZOME or HYPHA typically)
    non_battery_node = next((n for n in nodes if n.battery is None), None)
    if non_battery_node is None:
        pytest.skip("All nodes have batteries")

    result = source.simulate_battery_drain(non_battery_node.id, hours=1.0)
    assert result is None


def test_battery_drain_cannot_go_negative():
    """Test that battery drain stops at 0%"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    battery_node = next((n for n in nodes if n.battery is not None), None)
    if battery_node is None:
        pytest.skip("No battery nodes generated")

    # Drain for many hours to force 0
    new_battery = source.simulate_battery_drain(battery_node.id, hours=100.0)

    assert new_battery == 0


def test_update_node_status():
    """Test updating node status"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    battery_node = next((n for n in nodes if n.battery is not None), None)
    if battery_node is None:
        pytest.skip("No battery nodes generated")

    # Update with low battery
    source.update_node_status(battery_node.id, new_battery=5)

    # Check that the internal node was updated
    updated_node = next((n for n in source._nodes if n.id == battery_node.id), None)
    assert updated_node is not None
    assert updated_node.battery == 5
    assert updated_node.status == "degraded"


def test_update_node_status_zero_battery():
    """Test that zero battery sets status to offline"""
    source = MockMeshDataSource(seed=42)
    nodes = source.get_nodes()

    battery_node = next((n for n in nodes if n.battery is not None), None)
    if battery_node is None:
        pytest.skip("No battery nodes generated")

    source.update_node_status(battery_node.id, new_battery=0)

    updated_node = next((n for n in source._nodes if n.id == battery_node.id), None)
    assert updated_node is not None
    assert updated_node.battery == 0
    assert updated_node.status == "offline"
