"""
MYC3LIUM Intelligence Module
Sensor fusion, ATAK integration, collaborative mapping
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np


# ATAK CoT (Cursor on Target) protocol
class ATAKIntegration:
    """
    ATAK integration for tactical mapping
    Supports video/images, position tracking, intel sharing
    """

    def __init__(
        self, tak_server_url: str = "tcp://239.2.3.1:6969", security_manager=None
    ):
        self.tak_server = tak_server_url
        self.units = {}  # Track friendly units
        self.intel_items = []  # POIs, threats, etc.
        self.security = security_manager  # For message signing

    def create_cot_message(
        self,
        node_id: str,
        lat: float,
        lon: float,
        alt: float,
        unit_type: str = "a-f-G-E-S",
    ) -> str:
        """
        Create CoT (Cursor on Target) XML message for ATAK

        Args:
            node_id: Unique node identifier
            lat, lon, alt: Position
            unit_type: CoT type (a-f-G-E-S = friendly ground equipment sensor)

        Returns:
            XML string for ATAK
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        stale_time = datetime.utcnow().timestamp() + 300  # 5min stale

        cot_xml = f"""<?xml version="1.0"?>
<event version="2.0" uid="{node_id}" type="{unit_type}" time="{timestamp}" start="{timestamp}" stale="{stale_time}" how="m-g">
  <point lat="{lat}" lon="{lon}" hae="{alt}" ce="10.0" le="5.0"/>
  <detail>
    <contact callsign="MYC3L-{node_id[-4:]}"/>
    <link uid="{node_id}" relation="p-p"/>
    <precisionlocation geopointsrc="GPS"/>
    <track speed="0" course="0"/>
  </detail>
</event>"""

        return cot_xml

    def create_video_feed_cot(
        self,
        node_id: str,
        lat: float,
        lon: float,
        rtmp_url: str,
        sensor_fov: float = 45.0,
    ) -> str:
        """
        Create CoT message for video feed
        ATAK can display RTMP streams from mesh cameras
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        cot_xml = f"""<?xml version="1.0"?>
<event version="2.0" uid="{node_id}_video" type="b-m-p-s-p-loc" time="{timestamp}">
  <point lat="{lat}" lon="{lon}" hae="0"/>
  <detail>
    <contact callsign="CAM-{node_id[-4:]}"/>
    <link uid="{node_id}_video" relation="p-p" type="video"/>
    <__video url="{rtmp_url}" alias="MYC3LIUM Cam {node_id}">
      <ConnectionEntry networkTimeout="12000" uid="{node_id}_video" path="{rtmp_url}" protocol="rtmp" bufferTime="3000" address="{rtmp_url.split("//")[1].split(":")[0]}" port="{rtmp_url.split(":")[-1].split("/")[0]}" roverPort="-1" rtspReliable="0" ignoreEmbeddedKLV="false" alias="MYC3LIUM Cam {node_id}"/>
    </__video>
    <sensor fov="{sensor_fov}" model="OV3660" range="500"/>
  </detail>
</event>"""

        return cot_xml

    def create_image_cot(
        self,
        node_id: str,
        lat: float,
        lon: float,
        image_url: str,
        description: str = "",
    ) -> str:
        """
        Create CoT message for image attachment
        """
        datetime.utcnow().isoformat() + "Z"

        cot_xml = f"""<?xml version="1.0"?>
<event version="2.0" uid="{node_id}_img_{int(time.time())}" type="b-m-p-s-p-loc">
  <point lat="{lat}" lon="{lon}" hae="0"/>
  <detail>
    <contact callsign="IMG-{node_id[-4:]}"/>
    <remarks>{description}</remarks>
    <image>
      <url>{image_url}</url>
    </image>
  </detail>
</event>"""

        return cot_xml

    async def send_cot(self, cot_message: str, timeout: float = 3.0):
        """
        Send CoT message to ATAK server (multicast or TCP)
        Signed with HMAC if security manager provided
        """
        import socket

        # Sign message if security enabled
        if self.security:
            try:
                cot_message = self.security.sign_cot_message(cot_message)
            except Exception as e:
                print(f"CoT signing failed: {e}")
                return  # Don't send unsigned

        # Multicast implementation with timeout
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.settimeout(timeout)

            # ATAK default multicast group
            multicast_group = ("239.2.3.1", 6969)

            # Send in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, sock.sendto, cot_message.encode("utf-8"), multicast_group
            )

            sock.close()

        except socket.timeout:
            print(f"CoT send timeout to {multicast_group}")
        except Exception as e:
            print(f"CoT send error: {e}")

    async def update_unit_position(self, node_id: str, position: dict):
        """
        Push node position to ATAK
        """
        cot = self.create_cot_message(
            node_id, position["lat"], position["lon"], position.get("alt", 0)
        )

        await self.send_cot(cot)

    async def share_camera_feed(self, node_id: str, position: dict, rtmp_url: str):
        """
        Share camera feed to ATAK
        """
        cot = self.create_video_feed_cot(
            node_id, position["lat"], position["lon"], rtmp_url
        )

        await self.send_cot(cot)


@dataclass
class SensorFusionState:
    """Position estimate from multiple sensors"""

    lat: float
    lon: float
    alt: float
    velocity: float
    heading: float
    uncertainty: float  # meters
    timestamp: float
    sources: list[str]  # e.g., ['gps', 'rssi', 'tdoa']


class SensorFusion:
    """
    Fuse GPS, IMU, RSSI, TDOA for accurate positioning
    """

    def __init__(self):
        # State: [x, y, z, vx, vy, vz, heading]
        self.state = np.zeros(7)
        self.covariance = np.eye(7) * 100  # Initial uncertainty

        # Kalman filter matrices
        self.F = np.eye(7)  # State transition
        self.H_gps = np.zeros((3, 7))
        self.H_gps[0:3, 0:3] = np.eye(3)  # GPS measures position

        self.last_update = time.time()

    def update_gps(self, lat: float, lon: float, alt: float, accuracy: float):
        """
        GPS measurement update
        """
        # Convert lat/lon to local XY (simplified)
        x = lon * 111320 * np.cos(np.radians(lat))
        y = lat * 111320
        z = alt

        measurement = np.array([x, y, z])
        R = np.eye(3) * (accuracy**2)  # Measurement noise

        # Kalman update
        innovation = measurement - (self.H_gps @ self.state)
        S = self.H_gps @ self.covariance @ self.H_gps.T + R
        K = self.covariance @ self.H_gps.T @ np.linalg.inv(S)

        self.state = self.state + K @ innovation
        self.covariance = (np.eye(7) - K @ self.H_gps) @ self.covariance

        self.last_update = time.time()

    def update_rssi(self, anchors: list[tuple[str, float, float, float, float]]):
        """
        RSSI trilateration update

        Args:
            anchors: List of (node_id, lat, lon, alt, rssi)
        """
        if len(anchors) < 3:
            return  # Need at least 3 anchors

        # Convert RSSI to distance
        distances = []
        positions = []

        for node_id, lat, lon, alt, rssi in anchors:
            # Path loss model: RSSI = TX_POWER - 10*n*log10(d) - X
            TX_POWER = 17  # dBm
            PATH_LOSS_EXPONENT = 2.5  # Urban

            distance = 10 ** ((TX_POWER - rssi) / (10 * PATH_LOSS_EXPONENT))
            distances.append(distance)

            # Convert to XY
            x = lon * 111320 * np.cos(np.radians(lat))
            y = lat * 111320
            positions.append((x, y, alt))

        # Weighted least squares trilateration
        estimated_pos = self._trilaterate(positions, distances)

        # Update filter with lower confidence
        measurement = np.array([estimated_pos[0], estimated_pos[1], estimated_pos[2]])
        R = np.eye(3) * 25  # ±5m accuracy for RSSI

        innovation = measurement - (self.H_gps @ self.state)
        S = self.H_gps @ self.covariance @ self.H_gps.T + R
        K = self.covariance @ self.H_gps.T @ np.linalg.inv(S)

        self.state = self.state + K @ innovation
        self.covariance = (np.eye(7) - K @ self.H_gps) @ self.covariance

    def _trilaterate(
        self, positions: list, distances: list
    ) -> tuple[float, float, float]:
        """
        Weighted least squares trilateration
        """
        # Simplified 2D trilateration
        if len(positions) < 3:
            return (0, 0, 0)

        # Use first 3 anchors
        p1, p2, p3 = positions[:3]
        r1, r2, r3 = distances[:3]

        # Solve for intersection
        A = 2 * (p2[0] - p1[0])
        B = 2 * (p2[1] - p1[1])
        C = r1**2 - r2**2 - p1[0] ** 2 + p2[0] ** 2 - p1[1] ** 2 + p2[1] ** 2

        D = 2 * (p3[0] - p2[0])
        E = 2 * (p3[1] - p2[1])
        F = r2**2 - r3**2 - p2[0] ** 2 + p3[0] ** 2 - p2[1] ** 2 + p3[1] ** 2

        x = (C * E - F * B) / (E * A - B * D) if (E * A - B * D) != 0 else 0
        y = (C * D - A * F) / (B * D - A * E) if (B * D - A * E) != 0 else 0
        z = np.mean([p[2] for p in positions])

        return (x, y, z)

    def get_position(self) -> SensorFusionState:
        """
        Get current best position estimate
        """
        # Convert XY back to lat/lon
        x, y, z = self.state[0:3]

        lat = y / 111320
        lon = x / (111320 * np.cos(np.radians(lat)))

        velocity = np.linalg.norm(self.state[3:6])
        heading = self.state[6]
        uncertainty = np.sqrt(np.trace(self.covariance[0:3, 0:3]))

        return SensorFusionState(
            lat=lat,
            lon=lon,
            alt=z,
            velocity=velocity,
            heading=heading,
            uncertainty=uncertainty,
            timestamp=self.last_update,
            sources=["gps", "rssi"],  # Track which sensors contributed
        )


class IntelligenceGathering:
    """
    Collaborative intelligence gathering and sharing
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.observations = []
        self.rf_sources = []

    async def record_observation(
        self,
        obs_type: str,
        position: dict,
        metadata: dict,
        image_path: Optional[str] = None,
    ):
        """
        Record intelligence observation

        obs_type: 'poi', 'threat', 'obstacle', 'rf_source', etc.
        """
        observation = {
            "id": f"{self.node_id}_{int(time.time())}",
            "type": obs_type,
            "position": position,
            "metadata": metadata,
            "timestamp": time.time(),
            "image": image_path,
        }

        self.observations.append(observation)

        # Share to mesh via IPFS
        # await ipfs_node.publish_content(observation, priority='normal')

    async def detect_rf_source(
        self, frequency: float, rssi: float, estimated_position: Optional[dict] = None
    ):
        """
        Passive RF source detection
        """
        source = {
            "id": f"rf_{int(frequency)}_{int(time.time())}",
            "frequency": frequency,
            "rssi": rssi,
            "position": estimated_position,
            "detected_at": time.time(),
            "detector_node": self.node_id,
        }

        self.rf_sources.append(source)

    def get_heatmap_data(self, obs_type: str = "all") -> list[dict]:
        """
        Generate heatmap data for WebUI
        """
        if obs_type == "all":
            data = self.observations
        else:
            data = [obs for obs in self.observations if obs["type"] == obs_type]

        heatmap = []
        for obs in data:
            heatmap.append(
                {
                    "lat": obs["position"]["lat"],
                    "lon": obs["position"]["lon"],
                    "value": obs["metadata"].get("intensity", 1.0),
                    "timestamp": obs["timestamp"],
                }
            )

        return heatmap


# FastAPI endpoints for intelligence data
async def get_mesh_topology():
    """
    API endpoint: GET /api/intelligence/topology
    Returns current mesh topology for WebUI visualization
    """
    # Collect from BATMAN-adv
    # Return nodes + edges with link quality
    pass


async def get_position_history(node_id: str, hours: int = 1):
    """
    API endpoint: GET /api/intelligence/position/{node_id}?hours=1
    Returns position history for tracking
    """
    pass


async def get_intelligence_feed():
    """
    API endpoint: WebSocket /ws/intelligence
    Real-time intelligence updates
    """
    pass


if __name__ == "__main__":
    # Test ATAK integration
    atak = ATAKIntegration()

    # Create position update
    cot = atak.create_cot_message("m3l_spore_01", 47.6062, -122.3321, 125.0)
    print("Position CoT:")
    print(cot)

    # Create video feed
    video_cot = atak.create_video_feed_cot(
        "m3l_spore_01", 47.6062, -122.3321, "rtmp://192.168.1.100:1935/live/cam1"
    )
    print("\nVideo Feed CoT:")
    print(video_cot)
