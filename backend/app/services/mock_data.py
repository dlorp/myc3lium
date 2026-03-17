"""Mock data generation for MYC3LIUM mesh network simulation"""

import math
import random
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.models import Message, Node, SensorData, Thread


class MeshDataSource(ABC):
    """Abstract base class for mesh network data sources"""

    @abstractmethod
    def get_nodes(self) -> list[Node]:
        """Get all nodes in the mesh network"""
        pass

    @abstractmethod
    def get_threads(self) -> list[Thread]:
        """Get all threads (connections) in the mesh network"""
        pass

    @abstractmethod
    def get_messages(self) -> list[Message]:
        """Get all messages in the mesh network"""
        pass

    @abstractmethod
    def get_sensor_data(self, node_id: str) -> list[SensorData]:
        """Get sensor data for a specific node"""
        pass


class MockMeshDataSource(MeshDataSource):
    """Mock implementation of MeshDataSource for testing and development"""

    # Anchorage, Alaska GPS coordinates for 8 nodes
    ANCHORAGE_COORDS = [
        {"lat": 61.2181, "lon": -149.9003, "name": "Downtown"},  # Downtown Anchorage
        {"lat": 61.1919, "lon": -149.8478, "name": "Hillside"},  # Hillside area
        {"lat": 61.2147, "lon": -149.8947, "name": "Midtown"},  # Midtown
        {"lat": 61.1508, "lon": -149.8606, "name": "O'Malley"},  # O'Malley area
        {"lat": 61.2225, "lon": -149.8842, "name": "Airport"},  # Near Airport
        {"lat": 61.1944, "lon": -149.7661, "name": "Eagle River"},  # Eagle River
        {"lat": 61.1197, "lon": -149.9669, "name": "Girdwood"},  # Girdwood
        {"lat": 61.2489, "lon": -149.6856, "name": "JBER"},  # JBER base
    ]

    NODE_TYPES: list[Literal["SPORE", "HYPHA", "FROND", "RHIZOME"]] = [
        "HYPHA",
        "HYPHA",
        "FROND",
        "SPORE",
        "RHIZOME",
        "HYPHA",
        "FROND",
        "SPORE",
    ]

    # Thread configuration: (source_idx, target_idx, radio_type)
    THREAD_CONFIG: list[tuple[int, int, Literal["LoRa", "HaLow", "WiFi"]]] = [
        (0, 1, "LoRa"),  # Downtown <-> Hillside
        (0, 2, "WiFi"),  # Downtown <-> Midtown
        (1, 3, "LoRa"),  # Hillside <-> O'Malley
        (2, 4, "WiFi"),  # Midtown <-> Airport
        (2, 5, "HaLow"),  # Midtown <-> Eagle River
        (3, 6, "LoRa"),  # O'Malley <-> Girdwood
        (4, 7, "WiFi"),  # Airport <-> JBER
        (5, 7, "HaLow"),  # Eagle River <-> JBER
        (0, 4, "WiFi"),  # Downtown <-> Airport (backbone)
    ]

    def __init__(self, seed: int = 42, base_time: datetime | None = None):
        """
        Initialize mock data source

        Args:
            seed: Random seed for reproducibility
            base_time: Base timestamp for data generation (defaults to now)
        """
        self.rng = random.Random(seed)
        self.base_time = base_time or datetime.now(UTC)
        self._nodes: list[Node] = []
        self._threads: list[Thread] = []
        self._messages: list[Message] = []
        self._init_data()

    def _init_data(self):
        """Initialize all mock data"""
        self._generate_nodes()
        self._generate_threads()
        self._generate_messages()

    def _generate_nodes(self):
        """Generate 8 nodes with Anchorage coordinates and MYC3LIUM callsigns"""
        self._nodes = []
        for idx, (coord, node_type) in enumerate(zip(self.ANCHORAGE_COORDS, self.NODE_TYPES)):
            # Determine status based on seed and index
            status_roll = self.rng.random()
            if status_roll < 0.75:
                status = "online"
            elif status_roll < 0.95:
                status = "degraded"
            else:
                status = "offline"

            # Generate battery with some variance
            battery = None
            if node_type in ["SPORE", "FROND"]:  # Battery-powered nodes
                battery = max(10, min(100, int(85 - (idx * 5) + self.rng.randint(-10, 10))))

            # RSSI varies by status
            rssi = None
            if status == "online":
                rssi = self.rng.randint(-75, -45)
            elif status == "degraded":
                rssi = self.rng.randint(-95, -76)

            node = Node(
                id=f"myc3_{idx:03d}",
                type=node_type,
                callsign=f"MYC3LIUM-{coord['name'].upper().replace(' ', '-')}",
                status=status,
                rssi=rssi,
                battery=battery,
                last_seen=self.base_time - timedelta(seconds=self.rng.randint(0, 300)),
                position={"lat": coord["lat"], "lon": coord["lon"]},
            )
            self._nodes.append(node)

    def _generate_threads(self):
        """Generate 9 threads with different radio types"""
        self._threads = []
        for idx, (src_idx, tgt_idx, radio_type) in enumerate(self.THREAD_CONFIG):
            source_node = self._nodes[src_idx]
            target_node = self._nodes[tgt_idx]

            # Quality depends on radio type and node status
            base_quality = {"LoRa": 0.85, "HaLow": 0.80, "WiFi": 0.92}[radio_type]
            quality_variance = self.rng.uniform(-0.15, 0.10)
            quality = max(0.0, min(1.0, base_quality + quality_variance))

            # Degrade quality if either node is offline/degraded
            if source_node.status != "online" or target_node.status != "online":
                quality *= 0.6

            # RSSI varies by radio type
            rssi_ranges = {
                "LoRa": (-110, -85),
                "HaLow": (-105, -80),
                "WiFi": (-75, -50),
            }
            rssi = self.rng.randint(*rssi_ranges[radio_type])

            # Latency varies by radio type
            latency_ranges = {
                "LoRa": (50, 200),
                "HaLow": (30, 150),
                "WiFi": (5, 50),
            }
            latency = self.rng.randint(*latency_ranges[radio_type])

            thread = Thread(
                id=f"thread_{idx:03d}",
                source_id=source_node.id,
                target_id=target_node.id,
                radio_type=radio_type,
                rssi=rssi,
                quality=quality,
                latency=latency,
                established=self.base_time - timedelta(hours=self.rng.randint(1, 48)),
            )
            self._threads.append(thread)

    def _generate_messages(self):
        """Generate sample messages between nodes"""
        self._messages = []
        online_nodes = [n for n in self._nodes if n.status == "online"]

        if len(online_nodes) < 2:
            return

        message_templates = [
            "Status update: all systems operational",
            "Sensor reading nominal",
            "Battery check complete",
            "Network health good",
            "Uplink established",
        ]

        for idx in range(10):
            sender = self.rng.choice(online_nodes)
            recipient = self.rng.choice([n for n in online_nodes if n.id != sender.id])
            content = self.rng.choice(message_templates)
            hops = self.rng.randint(1, 3)

            message = Message(
                id=f"msg_{idx:06d}",
                sender_id=sender.id,
                recipient_id=recipient.id,
                content=content,
                timestamp=self.base_time - timedelta(minutes=self.rng.randint(0, 120)),
                hops=hops,
            )
            self._messages.append(message)

    def get_nodes(self) -> list[Node]:
        """Get all nodes in the mesh network"""
        return self._nodes.copy()

    def get_threads(self) -> list[Thread]:
        """Get all threads (connections) in the mesh network"""
        return self._threads.copy()

    def get_messages(self) -> list[Message]:
        """Get all messages in the mesh network"""
        return self._messages.copy()

    def get_sensor_data(self, node_id: str) -> list[SensorData]:
        """
        Generate sensor data for a specific node with diurnal temperature cycles

        Args:
            node_id: The node to generate sensor data for

        Returns:
            List of sensor data readings
        """
        node = next((n for n in self._nodes if n.id == node_id), None)
        if not node:
            return []

        sensor_data = []
        now = self.base_time

        # Generate temperature readings with diurnal cycle
        # Anchorage March temps: ~25°F to ~35°F (-4°C to 2°C)
        for hours_ago in range(24):
            timestamp = now - timedelta(hours=hours_ago)
            hour_of_day = timestamp.hour

            # Diurnal cycle: coldest at 6 AM, warmest at 3 PM
            base_temp = -1.0  # Average temp in Celsius
            amplitude = 3.0  # Temperature swing
            phase = (hour_of_day - 6) / 24 * 2 * math.pi  # Peak at 3 PM (hour 15)
            temp = base_temp + amplitude * math.sin(phase)

            # Add some random variance
            temp += self.rng.uniform(-0.5, 0.5)

            sensor_data.append(
                SensorData(
                    node_id=node_id,
                    sensor_type="temperature",
                    value=round(temp, 2),
                    unit="celsius",
                    timestamp=timestamp,
                )
            )

        # Add humidity reading
        humidity = self.rng.uniform(65, 85)  # Typical Anchorage humidity
        sensor_data.append(
            SensorData(
                node_id=node_id,
                sensor_type="humidity",
                value=round(humidity, 1),
                unit="percent",
                timestamp=now,
            )
        )

        # Add pressure reading
        pressure = self.rng.uniform(1010, 1020)  # Typical pressure in hPa
        sensor_data.append(
            SensorData(
                node_id=node_id,
                sensor_type="pressure",
                value=round(pressure, 1),
                unit="hPa",
                timestamp=now,
            )
        )

        return sensor_data

    def simulate_battery_drain(self, node_id: str, hours: float = 1.0) -> int | None:
        """
        Simulate battery drain for a node over time

        Args:
            node_id: The node to simulate
            hours: Number of hours of drain to simulate

        Returns:
            New battery level, or None if node has no battery
        """
        node = next((n for n in self._nodes if n.id == node_id), None)
        if not node or node.battery is None:
            return None

        # Drain rate depends on node type
        drain_rates = {
            "SPORE": 2.0,  # 2% per hour (sensor node)
            "FROND": 3.5,  # 3.5% per hour (camera node)
            "HYPHA": 1.0,  # 1% per hour (relay, lower power)
            "RHIZOME": 0.5,  # 0.5% per hour (base station, minimal drain)
        }

        drain_rate = drain_rates.get(node.type, 2.0)
        drain_amount = drain_rate * hours

        # Add some randomness (±10%)
        drain_amount *= self.rng.uniform(0.9, 1.1)

        new_battery = max(0, int(node.battery - drain_amount))
        return new_battery

    def update_node_status(self, node_id: str, new_battery: int | None = None):
        """
        Update a node's status based on battery or other factors

        Args:
            node_id: The node to update
            new_battery: New battery level (if applicable)
        """
        for node in self._nodes:
            if node.id == node_id:
                if new_battery is not None:
                    node.battery = new_battery
                    # Update status based on battery
                    if new_battery == 0:
                        node.status = "offline"
                    elif new_battery < 10:
                        node.status = "degraded"
                node.last_seen = datetime.now(UTC)
                break
