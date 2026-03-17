"""Tests for new Phase 2 Pydantic models"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import CameraStream, SatellitePass, SystemStatus, Thread


def test_thread_valid():
    """Test valid Thread creation"""
    thread = Thread(
        id="thread_001",
        source_id="node_001",
        target_id="node_002",
        radio_type="LoRa",
        rssi=-72,
        quality=0.85,
        latency=25,
    )

    assert thread.id == "thread_001"
    assert thread.source_id == "node_001"
    assert thread.target_id == "node_002"
    assert thread.radio_type == "LoRa"
    assert thread.rssi == -72
    assert thread.quality == 0.85
    assert thread.latency == 25
    assert isinstance(thread.established, datetime)


def test_thread_radio_types():
    """Test all valid radio types for Thread"""
    radio_types = ["LoRa", "HaLow", "WiFi"]

    for radio_type in radio_types:
        thread = Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type=radio_type,
            quality=0.8,
        )
        assert thread.radio_type == radio_type

    # Invalid radio type
    with pytest.raises(ValidationError):
        Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type="Bluetooth",
            quality=0.8,
        )


def test_thread_quality_range():
    """Test Thread quality validation (0.0-1.0)"""
    # Valid quality values
    for quality in [0.0, 0.5, 1.0]:
        thread = Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type="WiFi",
            quality=quality,
        )
        assert thread.quality == quality

    # Invalid quality (out of range)
    with pytest.raises(ValidationError):
        Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type="WiFi",
            quality=1.5,
        )

    with pytest.raises(ValidationError):
        Thread(
            id="thread_001",
            source_id="node_001",
            target_id="node_002",
            radio_type="WiFi",
            quality=-0.1,
        )


def test_thread_optional_fields():
    """Test Thread with optional fields"""
    thread = Thread(
        id="thread_001",
        source_id="node_001",
        target_id="node_002",
        radio_type="LoRa",
        quality=0.75,
    )

    assert thread.rssi is None
    assert thread.latency is None


def test_satellite_pass_valid():
    """Test valid SatellitePass creation"""
    aos = datetime(2026, 3, 16, 14, 23, 0, tzinfo=timezone.utc)
    los = datetime(2026, 3, 16, 14, 35, 0, tzinfo=timezone.utc)

    sat_pass = SatellitePass(
        id="pass_001",
        name="NOAA 19",
        aos=aos,
        los=los,
        max_elevation=45.2,
        azimuth_aos=15.5,
        azimuth_los=195.3,
    )

    assert sat_pass.id == "pass_001"
    assert sat_pass.name == "NOAA 19"
    assert sat_pass.aos == aos
    assert sat_pass.los == los
    assert sat_pass.max_elevation == 45.2
    assert sat_pass.azimuth_aos == 15.5
    assert sat_pass.azimuth_los == 195.3


def test_satellite_pass_elevation_range():
    """Test SatellitePass max_elevation validation (0.0-90.0)"""
    aos = datetime(2026, 3, 16, 14, 23, 0, tzinfo=timezone.utc)
    los = datetime(2026, 3, 16, 14, 35, 0, tzinfo=timezone.utc)

    # Valid elevations
    for elevation in [0.0, 45.0, 90.0]:
        sat_pass = SatellitePass(
            id="pass_001", name="Test Sat", aos=aos, los=los, max_elevation=elevation
        )
        assert sat_pass.max_elevation == elevation

    # Invalid elevation (out of range)
    with pytest.raises(ValidationError):
        SatellitePass(id="pass_001", name="Test Sat", aos=aos, los=los, max_elevation=95.0)

    with pytest.raises(ValidationError):
        SatellitePass(id="pass_001", name="Test Sat", aos=aos, los=los, max_elevation=-5.0)


def test_satellite_pass_azimuth_range():
    """Test SatellitePass azimuth validation (0.0-360.0)"""
    aos = datetime(2026, 3, 16, 14, 23, 0, tzinfo=timezone.utc)
    los = datetime(2026, 3, 16, 14, 35, 0, tzinfo=timezone.utc)

    # Valid azimuths
    sat_pass = SatellitePass(
        id="pass_001",
        name="Test Sat",
        aos=aos,
        los=los,
        max_elevation=45.0,
        azimuth_aos=0.0,
        azimuth_los=360.0,
    )
    assert sat_pass.azimuth_aos == 0.0
    assert sat_pass.azimuth_los == 360.0

    # Invalid azimuth
    with pytest.raises(ValidationError):
        SatellitePass(
            id="pass_001",
            name="Test Sat",
            aos=aos,
            los=los,
            max_elevation=45.0,
            azimuth_aos=365.0,
        )


def test_satellite_pass_optional_azimuths():
    """Test SatellitePass with optional azimuth fields"""
    aos = datetime(2026, 3, 16, 14, 23, 0, tzinfo=timezone.utc)
    los = datetime(2026, 3, 16, 14, 35, 0, tzinfo=timezone.utc)

    sat_pass = SatellitePass(id="pass_001", name="Test Sat", aos=aos, los=los, max_elevation=45.0)

    assert sat_pass.azimuth_aos is None
    assert sat_pass.azimuth_los is None


def test_camera_stream_valid():
    """Test valid CameraStream creation"""
    camera = CameraStream(
        id="cam_001",
        node_id="node_003",
        name="North Ridge Camera",
        stream_url="rtsp://10.0.1.50:554/stream",
        status="active",
        resolution="1920x1080",
        fps=30,
        last_frame=datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert camera.id == "cam_001"
    assert camera.node_id == "node_003"
    assert camera.name == "North Ridge Camera"
    assert camera.stream_url == "rtsp://10.0.1.50:554/stream"
    assert camera.status == "active"
    assert camera.resolution == "1920x1080"
    assert camera.fps == 30
    assert camera.last_frame == datetime(2026, 3, 16, 12, 0, 0, tzinfo=timezone.utc)


def test_camera_stream_status_types():
    """Test all valid status types for CameraStream"""
    statuses = ["active", "inactive", "error"]

    for status in statuses:
        camera = CameraStream(
            id="cam_001",
            node_id="node_003",
            name="Test Camera",
            stream_url="rtsp://10.0.1.50:554/stream",
            status=status,
        )
        assert camera.status == status

    # Invalid status
    with pytest.raises(ValidationError):
        CameraStream(
            id="cam_001",
            node_id="node_003",
            name="Test Camera",
            stream_url="rtsp://10.0.1.50:554/stream",
            status="unknown",
        )


def test_camera_stream_fps_range():
    """Test CameraStream FPS validation (1-120)"""
    # Valid FPS values
    for fps in [1, 30, 60, 120]:
        camera = CameraStream(
            id="cam_001",
            node_id="node_003",
            name="Test Camera",
            stream_url="rtsp://10.0.1.50:554/stream",
            status="active",
            fps=fps,
        )
        assert camera.fps == fps

    # Invalid FPS (out of range)
    with pytest.raises(ValidationError):
        CameraStream(
            id="cam_001",
            node_id="node_003",
            name="Test Camera",
            stream_url="rtsp://10.0.1.50:554/stream",
            status="active",
            fps=0,
        )

    with pytest.raises(ValidationError):
        CameraStream(
            id="cam_001",
            node_id="node_003",
            name="Test Camera",
            stream_url="rtsp://10.0.1.50:554/stream",
            status="active",
            fps=150,
        )


def test_camera_stream_optional_fields():
    """Test CameraStream with optional fields"""
    camera = CameraStream(
        id="cam_001",
        node_id="node_003",
        name="Test Camera",
        stream_url="rtsp://10.0.1.50:554/stream",
        status="inactive",
    )

    assert camera.resolution is None
    assert camera.fps is None
    assert camera.last_frame is None


def test_system_status_valid():
    """Test valid SystemStatus creation"""
    status = SystemStatus(
        uptime_seconds=86400,
        node_count=8,
        active_node_count=7,
        thread_count=9,
        message_count=1542,
        health="healthy",
    )

    assert status.uptime_seconds == 86400
    assert status.node_count == 8
    assert status.active_node_count == 7
    assert status.thread_count == 9
    assert status.message_count == 1542
    assert status.health == "healthy"
    assert isinstance(status.last_update, datetime)


def test_system_status_health_types():
    """Test all valid health types for SystemStatus"""
    health_types = ["healthy", "degraded", "critical"]

    for health in health_types:
        status = SystemStatus(
            uptime_seconds=100,
            node_count=5,
            active_node_count=4,
            thread_count=3,
            message_count=10,
            health=health,
        )
        assert status.health == health

    # Invalid health
    with pytest.raises(ValidationError):
        SystemStatus(
            uptime_seconds=100,
            node_count=5,
            active_node_count=4,
            thread_count=3,
            message_count=10,
            health="unknown",
        )


def test_system_status_non_negative():
    """Test SystemStatus non-negative field validation"""
    # Valid values
    status = SystemStatus(
        uptime_seconds=0,
        node_count=0,
        active_node_count=0,
        thread_count=0,
        message_count=0,
        health="critical",
    )
    assert status.uptime_seconds == 0

    # Invalid negative values
    with pytest.raises(ValidationError):
        SystemStatus(
            uptime_seconds=-100,
            node_count=5,
            active_node_count=4,
            thread_count=3,
            message_count=10,
            health="healthy",
        )

    with pytest.raises(ValidationError):
        SystemStatus(
            uptime_seconds=100,
            node_count=-5,
            active_node_count=4,
            thread_count=3,
            message_count=10,
            health="healthy",
        )
