"""Tests for Pydantic models"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import Connection, Message, Node, NodeUpdate, SensorData


def test_node_valid():
    """Test valid Node creation"""
    node = Node(
        id="node_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
        rssi=-65,
        battery=87
    )

    assert node.id == "node_001"
    assert node.type == "HYPHA"
    assert node.callsign == "test-node"
    assert node.status == "online"
    assert node.rssi == -65
    assert node.battery == 87
    assert isinstance(node.last_seen, datetime)


def test_node_invalid_type():
    """Test Node with invalid type"""
    with pytest.raises(ValidationError):
        Node(
            id="node_001",
            type="INVALID_TYPE",
            callsign="test-node",
            status="online"
        )


def test_node_invalid_status():
    """Test Node with invalid status"""
    with pytest.raises(ValidationError):
        Node(
            id="node_001",
            type="HYPHA",
            callsign="test-node",
            status="unknown"
        )


def test_node_battery_range():
    """Test Node battery validation"""
    # Valid battery
    node = Node(
        id="node_001",
        type="HYPHA",
        callsign="test-node",
        status="online",
        battery=50
    )
    assert node.battery == 50

    # Invalid battery (out of range)
    with pytest.raises(ValidationError):
        Node(
            id="node_001",
            type="HYPHA",
            callsign="test-node",
            status="online",
            battery=150
        )


def test_node_optional_fields():
    """Test Node with optional fields"""
    node = Node(
        id="node_001",
        type="SPORE",
        callsign="minimal-node",
        status="offline"
    )

    assert node.rssi is None
    assert node.battery is None
    assert node.position is None


def test_connection_valid():
    """Test valid Connection creation"""
    conn = Connection(
        source_id="node_001",
        target_id="node_002",
        quality=0.92,
        latency=15
    )

    assert conn.source_id == "node_001"
    assert conn.target_id == "node_002"
    assert conn.quality == 0.92
    assert conn.latency == 15


def test_connection_quality_range():
    """Test Connection quality validation"""
    # Valid quality
    conn = Connection(
        source_id="node_001",
        target_id="node_002",
        quality=0.5
    )
    assert conn.quality == 0.5

    # Invalid quality (out of range)
    with pytest.raises(ValidationError):
        Connection(
            source_id="node_001",
            target_id="node_002",
            quality=1.5
        )


def test_sensor_data_valid():
    """Test valid SensorData creation"""
    sensor = SensorData(
        node_id="node_003",
        sensor_type="temperature",
        value=22.5,
        unit="celsius"
    )

    assert sensor.node_id == "node_003"
    assert sensor.sensor_type == "temperature"
    assert sensor.value == 22.5
    assert sensor.unit == "celsius"


def test_message_valid():
    """Test valid Message creation"""
    msg = Message(
        id="msg_001",
        sender_id="node_001",
        recipient_id="node_005",
        content="Test message",
        hops=2
    )

    assert msg.id == "msg_001"
    assert msg.sender_id == "node_001"
    assert msg.recipient_id == "node_005"
    assert msg.content == "Test message"
    assert msg.hops == 2


def test_message_broadcast():
    """Test Message with no recipient (broadcast)"""
    msg = Message(
        id="msg_002",
        sender_id="node_001",
        content="Broadcast message"
    )

    assert msg.recipient_id is None
    assert msg.hops == 0


def test_node_update_valid():
    """Test valid NodeUpdate creation"""
    update = NodeUpdate(
        event="node_update",
        data={"id": "node_001", "status": "degraded"}
    )

    assert update.event == "node_update"
    assert update.data["id"] == "node_001"
    assert isinstance(update.timestamp, datetime)


def test_node_update_event_types():
    """Test all NodeUpdate event types"""
    events = ["node_update", "node_added", "node_removed", "connection_update"]

    for event in events:
        update = NodeUpdate(event=event, data={})
        assert update.event == event

    # Invalid event
    with pytest.raises(ValidationError):
        NodeUpdate(event="invalid_event", data={})
