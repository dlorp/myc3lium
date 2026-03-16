"""Pydantic models for MYC3LIUM API"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    """Mesh network node"""

    id: str = Field(..., max_length=64, description="Unique node identifier")
    type: Literal["SPORE", "HYPHA", "FROND", "RHIZOME"] = Field(
        ..., description="Node type in mycelial network"
    )
    callsign: str = Field(..., max_length=32, description="Human-readable node identifier")
    status: Literal["online", "offline", "degraded"] = Field(
        ..., description="Current node status"
    )
    rssi: int | None = Field(None, description="Signal strength (dBm)")
    battery: int | None = Field(None, ge=0, le=100, description="Battery percentage")
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
    position: dict[str, float] | None = Field(None, description="Geographic coordinates (lat/lon)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "node_001",
                "type": "HYPHA",
                "callsign": "relay-alpha",
                "status": "online",
                "rssi": -65,
                "battery": 87,
                "last_seen": "2026-03-16T12:00:00Z",
                "position": {"lat": 61.2181, "lon": -149.9003}
            }
        }
    )


class Connection(BaseModel):
    """Connection between two nodes"""

    source_id: str = Field(..., max_length=64, description="Source node ID")
    target_id: str = Field(..., max_length=64, description="Target node ID")
    quality: float = Field(..., ge=0.0, le=1.0, description="Connection quality (0-1)")
    latency: int | None = Field(None, description="Latency in milliseconds")
    established: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Connection established time",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "node_001",
                "target_id": "node_002",
                "quality": 0.92,
                "latency": 15,
                "established": "2026-03-16T12:00:00Z"
            }
        }
    )


class SensorData(BaseModel):
    """Environmental sensor reading"""

    node_id: str = Field(..., max_length=64, description="Node that collected the data")
    sensor_type: str = Field(
        ..., max_length=32, description="Type of sensor (temperature, humidity, etc)"
    )
    value: float = Field(..., description="Sensor reading value")
    unit: str = Field(..., max_length=16, description="Unit of measurement")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Reading timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_id": "node_003",
                "sensor_type": "temperature",
                "value": 22.5,
                "unit": "celsius",
                "timestamp": "2026-03-16T12:00:00Z"
            }
        }
    )


class Message(BaseModel):
    """Mesh network message"""

    id: str = Field(..., max_length=64, description="Message identifier")
    sender_id: str = Field(..., max_length=64, description="Sending node ID")
    recipient_id: str | None = Field(
        None, max_length=64, description="Target node ID (null for broadcast)"
    )
    content: str = Field(..., max_length=1024, description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Message timestamp"
    )
    hops: int = Field(0, ge=0, description="Number of hops to destination")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "msg_001",
                "sender_id": "node_001",
                "recipient_id": "node_005",
                "content": "Status update: all systems operational",
                "timestamp": "2026-03-16T12:00:00Z",
                "hops": 2
            }
        }
    )


class NodeUpdate(BaseModel):
    """WebSocket node update message"""

    event: Literal["node_update", "node_added", "node_removed", "connection_update"] = Field(
        ..., description="Event type"
    )
    data: dict = Field(..., description="Event payload")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Event timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event": "node_update",
                "data": {
                    "id": "node_001",
                    "status": "degraded",
                    "battery": 15
                },
                "timestamp": "2026-03-16T12:00:00Z"
            }
        }
    )
