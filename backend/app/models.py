"""Pydantic models for MYC3LIUM API"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Node(BaseModel):
    """Mesh network node"""

    id: str = Field(..., max_length=64, description="Unique node identifier")
    type: Literal["SPORE", "HYPHA", "FROND", "RHIZOME"] = Field(
        ..., description="Node type in mycelial network"
    )
    callsign: str = Field(
        ..., max_length=32, description="Human-readable node identifier"
    )
    status: Literal["online", "offline", "degraded"] = Field(
        ..., description="Current node status"
    )
    rssi: Optional[int] = Field(None, description="Signal strength (dBm)")
    battery: Optional[int] = Field(None, ge=0, le=100, description="Battery percentage")
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )
    position: Optional[dict[str, float]] = Field(
        None, description="Geographic coordinates (lat/lon)"
    )

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
                "position": {"lat": 61.2181, "lon": -149.9003},
            }
        }
    )


class Connection(BaseModel):
    """Connection between two nodes"""

    source_id: str = Field(..., max_length=64, description="Source node ID")
    target_id: str = Field(..., max_length=64, description="Target node ID")
    quality: float = Field(..., ge=0.0, le=1.0, description="Connection quality (0-1)")
    latency: Optional[int] = Field(None, description="Latency in milliseconds")
    established: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Connection established time",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "node_001",
                "target_id": "node_002",
                "quality": 0.92,
                "latency": 15,
                "established": "2026-03-16T12:00:00Z",
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
        default_factory=lambda: datetime.now(timezone.utc),
        description="Reading timestamp",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_id": "node_003",
                "sensor_type": "temperature",
                "value": 22.5,
                "unit": "celsius",
                "timestamp": "2026-03-16T12:00:00Z",
            }
        }
    )


class Message(BaseModel):
    """Mesh network message"""

    id: str = Field(..., max_length=64, description="Message identifier")
    sender_id: str = Field(..., max_length=64, description="Sending node ID")
    recipient_id: Optional[str] = Field(
        None, max_length=64, description="Target node ID (null for broadcast)"
    )
    content: str = Field(..., max_length=1024, description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message timestamp",
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
                "hops": 2,
            }
        }
    )


class NodeUpdate(BaseModel):
    """WebSocket node update message"""

    event: Literal["node_update", "node_added", "node_removed", "connection_update"] = (
        Field(..., description="Event type")
    )
    data: dict = Field(..., description="Event payload")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event": "node_update",
                "data": {"id": "node_001", "status": "degraded", "battery": 15},
                "timestamp": "2026-03-16T12:00:00Z",
            }
        }
    )


class Thread(BaseModel):
    """Mesh network connection thread (radio link between nodes)"""

    id: str = Field(..., max_length=64, description="Unique thread identifier")
    source_id: str = Field(..., max_length=64, description="Source node ID")
    target_id: str = Field(..., max_length=64, description="Target node ID")
    radio_type: Literal["LoRa", "HaLow", "WiFi"] = Field(
        ..., description="Radio technology type"
    )
    rssi: Optional[int] = Field(None, description="Signal strength (dBm)")
    quality: float = Field(..., ge=0.0, le=1.0, description="Connection quality (0-1)")
    latency: Optional[int] = Field(None, description="Latency in milliseconds")
    established: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Thread established time",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "thread_001",
                "source_id": "node_001",
                "target_id": "node_002",
                "radio_type": "LoRa",
                "rssi": -72,
                "quality": 0.85,
                "latency": 25,
                "established": "2026-03-16T12:00:00Z",
            }
        }
    )


class SatellitePass(BaseModel):
    """Satellite pass prediction"""

    id: str = Field(..., max_length=64, description="Unique pass identifier")
    name: str = Field(..., max_length=64, description="Satellite name")
    aos: datetime = Field(..., description="Acquisition of Signal (rise time)")
    los: datetime = Field(..., description="Loss of Signal (set time)")
    max_elevation: float = Field(
        ..., ge=0.0, le=90.0, description="Maximum elevation in degrees"
    )
    azimuth_aos: Optional[float] = Field(
        None, ge=0.0, le=360.0, description="Azimuth at AOS"
    )
    azimuth_los: Optional[float] = Field(
        None, ge=0.0, le=360.0, description="Azimuth at LOS"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "pass_001",
                "name": "NOAA 19",
                "aos": "2026-03-16T14:23:00Z",
                "los": "2026-03-16T14:35:00Z",
                "max_elevation": 45.2,
                "azimuth_aos": 15.5,
                "azimuth_los": 195.3,
            }
        }
    )


class CameraStream(BaseModel):
    """Camera stream information"""

    id: str = Field(..., max_length=64, description="Unique camera identifier")
    node_id: str = Field(..., max_length=64, description="Node hosting the camera")
    name: str = Field(..., max_length=128, description="Human-readable camera name")
    stream_url: str = Field(..., max_length=512, description="Camera stream URL")
    status: Literal["active", "inactive", "error"] = Field(
        ..., description="Stream status"
    )
    resolution: Optional[str] = Field(
        None, max_length=32, description="Stream resolution (e.g., 1920x1080)"
    )
    fps: Optional[int] = Field(None, ge=1, le=120, description="Frames per second")
    last_frame: Optional[datetime] = Field(
        None, description="Timestamp of last received frame"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "cam_001",
                "node_id": "node_003",
                "name": "North Ridge Camera",
                "stream_url": "rtsp://10.0.1.50:554/stream",
                "status": "active",
                "resolution": "1920x1080",
                "fps": 30,
                "last_frame": "2026-03-16T12:00:00Z",
            }
        }
    )


class SystemStatus(BaseModel):
    """Overall mesh network system status"""

    uptime_seconds: int = Field(..., ge=0, description="System uptime in seconds")
    node_count: int = Field(..., ge=0, description="Total number of nodes")
    active_node_count: int = Field(..., ge=0, description="Number of online nodes")
    thread_count: int = Field(
        ..., ge=0, description="Total number of threads (connections)"
    )
    message_count: int = Field(..., ge=0, description="Total messages processed")
    last_update: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last status update",
    )
    health: Literal["healthy", "degraded", "critical"] = Field(
        ..., description="Overall system health"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uptime_seconds": 86400,
                "node_count": 8,
                "active_node_count": 7,
                "thread_count": 9,
                "message_count": 1542,
                "last_update": "2026-03-16T12:00:00Z",
                "health": "healthy",
            }
        }
    )
