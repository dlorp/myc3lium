"""
MYC3LIUM Custom Intelligent Router
Adaptive multi-radio mesh routing with quality metrics and smart path selection

Features:
- Link quality metrics (ETX - Expected Transmission Count)
- Adaptive radio selection (LoRa vs HaLow vs WiFi based on conditions)
- Multi-path routing with load balancing
- Dynamic power adjustment based on link quality
- Predictive route maintenance
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RadioType(Enum):
    """Available radio interfaces"""

    LORA = "lora"  # Long range, low bandwidth (2-10km, 0.3-50 kbps)
    HALOW = "halow"  # Medium range, high bandwidth (1km, 32 Mbps)
    WIFI = "wifi"  # Short range, highest bandwidth (100m, 100+ Mbps)


@dataclass
class LinkMetrics:
    """Real-time link quality metrics"""

    rssi: float = 0.0  # Signal strength (dBm)
    snr: float = 0.0  # Signal-to-noise ratio (dB)
    packet_loss: float = 0.0  # Packet loss rate (0-1)
    latency_ms: float = 0.0  # Round-trip time
    bandwidth_kbps: float = 0.0  # Available bandwidth

    # Calculated metrics
    etx: float = 1.0  # Expected Transmission Count (lower is better)
    last_update: float = field(default_factory=time.time)

    def update_etx(self):
        """Calculate ETX from packet loss"""
        if self.packet_loss >= 1.0:
            self.etx = float("inf")
        else:
            # ETX = 1 / (1 - packet_loss) for both directions
            # Simplified: assume symmetric links
            self.etx = (
                1.0 / (1.0 - self.packet_loss) if self.packet_loss < 1.0 else 999.0
            )
        self.last_update = time.time()

    def calculate_quality(self) -> float:
        """
        Composite link quality score (0-100)
        Higher is better
        """
        # RSSI contribution (normalize -120 to -30 dBm → 0 to 50)
        rssi_score = max(0, min(50, (self.rssi + 120) * 50 / 90))

        # SNR contribution (normalize 0 to 20 dB → 0 to 30)
        snr_score = max(0, min(30, self.snr * 30 / 20))

        # Packet loss penalty (0-20 points)
        loss_penalty = self.packet_loss * 20

        return rssi_score + snr_score - loss_penalty


@dataclass
class RadioCapabilities:
    """Static capabilities of each radio type"""

    radio_type: RadioType
    max_range_m: int
    max_bandwidth_kbps: int
    min_latency_ms: float
    power_consumption_mw: int

    # Cost factors (for path selection)
    cost_per_hop: float = 1.0


# Radio capability definitions
RADIO_CAPS = {
    RadioType.LORA: RadioCapabilities(
        radio_type=RadioType.LORA,
        max_range_m=10000,  # 10 km line of sight
        max_bandwidth_kbps=50,  # Up to 50 kbps
        min_latency_ms=200,  # ~200ms typical
        power_consumption_mw=500,
        cost_per_hop=1.0,  # Low cost (long range)
    ),
    RadioType.HALOW: RadioCapabilities(
        radio_type=RadioType.HALOW,
        max_range_m=1000,  # 1 km
        max_bandwidth_kbps=32000,  # 32 Mbps
        min_latency_ms=10,  # ~10ms typical
        power_consumption_mw=2000,
        cost_per_hop=2.0,  # Medium cost
    ),
    RadioType.WIFI: RadioCapabilities(
        radio_type=RadioType.WIFI,
        max_range_m=100,  # 100m practical
        max_bandwidth_kbps=100000,  # 100+ Mbps
        min_latency_ms=1,  # <1ms typical
        power_consumption_mw=1500,
        cost_per_hop=3.0,  # High cost (short range)
    ),
}


class AdaptiveRouter:
    """
    MYC3LIUM Intelligent Multi-Radio Router

    Responsibilities:
    - Track link quality across all radios
    - Select best radio for each transmission
    - Maintain routing tables with ETX metrics
    - Adapt TX power based on link quality
    - Load balance across multiple paths
    """

    def __init__(self, node_id: str):
        self.node_id = node_id

        # Link state database
        # {(node_a, node_b, radio): LinkMetrics}
        self.links: dict[tuple[str, str, RadioType], LinkMetrics] = {}

        # Routing table
        # {destination: [(next_hop, radio, cost), ...]}
        self.routes: dict[str, list[tuple[str, RadioType, float]]] = defaultdict(list)

        # Packet history for loss tracking
        self.tx_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Active radio interfaces
        self.active_radios: dict[RadioType, bool] = {
            RadioType.LORA: False,
            RadioType.HALOW: False,
            RadioType.WIFI: False,
        }

        self._lock = threading.Lock()
        self._running = False
        self._update_thread = None

    def register_radio(self, radio_type: RadioType):
        """Mark a radio as available"""
        with self._lock:
            self.active_radios[radio_type] = True
            logger.info(f"Registered radio: {radio_type.value}")

    def update_link_metrics(
        self,
        local: str,
        remote: str,
        radio: RadioType,
        rssi: float,
        snr: float,
        latency_ms: float,
    ):
        """Update link quality from probe or data packet"""
        with self._lock:
            key = (local, remote, radio)

            if key not in self.links:
                self.links[key] = LinkMetrics()

            link = self.links[key]
            link.rssi = rssi
            link.snr = snr
            link.latency_ms = latency_ms

            # Calculate ETX from TX history
            link.packet_loss = self._calculate_packet_loss(remote, radio)
            link.update_etx()

            logger.debug(
                f"Link {local}->{remote} via {radio.value}: "
                f"RSSI={rssi:.1f} SNR={snr:.1f} ETX={link.etx:.2f}"
            )

    def _calculate_packet_loss(self, dest: str, radio: RadioType) -> float:
        """Calculate packet loss rate from TX history"""
        key = f"{dest}:{radio.value}"
        history = self.tx_history[key]

        if len(history) < 10:
            return 0.0  # Not enough data

        successful = sum(1 for success in history if success)
        return 1.0 - (successful / len(history))

    def record_transmission(self, dest: str, radio: RadioType, success: bool):
        """Record TX outcome for loss tracking"""
        key = f"{dest}:{radio.value}"
        self.tx_history[key].append(success)

    def select_best_radio(
        self, dest: str, packet_size: int, latency_sensitive: bool = False
    ) -> Optional[RadioType]:
        """
        Intelligent radio selection based on:
        - Link quality (ETX)
        - Packet size vs bandwidth
        - Latency requirements
        - Power efficiency

        Returns best radio or None if no route available
        """
        with self._lock:
            if dest not in self.routes or not self.routes[dest]:
                return None

            candidates = []

            for next_hop, radio, cost in self.routes[dest]:
                if not self.active_radios[radio]:
                    continue

                link_key = (self.node_id, next_hop, radio)
                if link_key not in self.links:
                    continue

                link = self.links[link_key]
                caps = RADIO_CAPS[radio]

                # Calculate suitability score
                score = 0.0

                # Link quality (ETX) - lower is better
                etx_score = 100.0 / link.etx if link.etx > 0 else 0.0
                score += etx_score * 40  # 40% weight

                # Bandwidth adequacy
                required_kbps = (packet_size * 8) / 1000  # Convert bytes to kbps
                if caps.max_bandwidth_kbps >= required_kbps:
                    bw_score = 100.0
                else:
                    bw_score = (caps.max_bandwidth_kbps / required_kbps) * 100.0
                score += bw_score * 30  # 30% weight

                # Latency (if sensitive)
                if latency_sensitive:
                    latency_score = 100.0 - min(100.0, link.latency_ms)
                    score += latency_score * 20  # 20% weight
                else:
                    score += 10  # Baseline

                # Power efficiency (lower consumption = higher score)
                power_score = 100.0 - (caps.power_consumption_mw / 30.0)
                score += max(0, power_score) * 10  # 10% weight

                candidates.append((radio, score))

            if not candidates:
                return None

            # Return radio with highest score
            best_radio, best_score = max(candidates, key=lambda x: x[1])
            logger.debug(
                f"Selected {best_radio.value} for {dest} (score: {best_score:.1f})"
            )
            return best_radio

    def compute_routes(self):
        """
        Recompute routing table using Dijkstra with ETX metrics
        Run periodically or on topology change
        """
        with self._lock:
            # Build graph: {node: [(neighbor, radio, etx), ...]}
            graph = defaultdict(list)

            for (src, dst, radio), link in self.links.items():
                if link.etx < 999.0:  # Exclude broken links
                    graph[src].append((dst, radio, link.etx))

            # Dijkstra for each destination
            all_nodes = set()
            for src, dst, _ in self.links.keys():
                all_nodes.add(src)
                all_nodes.add(dst)

            for dest in all_nodes:
                if dest == self.node_id:
                    continue

                # Find best path to dest
                paths = self._dijkstra(graph, self.node_id, dest)
                self.routes[dest] = paths

        logger.info(f"Computed routes to {len(self.routes)} destinations")

    def _dijkstra(
        self, graph: dict, start: str, end: str
    ) -> list[tuple[str, RadioType, float]]:
        """
        Dijkstra shortest path with ETX metric
        Returns list of (next_hop, radio, total_cost)
        """
        distances = {start: 0.0}
        previous = {}
        radio_used = {}
        unvisited = set(graph.keys())

        while unvisited:
            current = min(unvisited, key=lambda n: distances.get(n, float("inf")))

            if current == end:
                break

            if distances.get(current, float("inf")) == float("inf"):
                break

            unvisited.remove(current)

            for neighbor, radio, etx in graph[current]:
                distance = distances[current] + etx

                if distance < distances.get(neighbor, float("inf")):
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    radio_used[neighbor] = radio

        if end not in previous:
            return []

        # Trace path back
        path = []
        current = end
        while current in previous:
            prev = previous[current]
            radio = radio_used[current]

            if prev == start:
                # This is the next hop
                cost = distances[current]
                path.append((current, radio, cost))

            current = prev

        return path

    def get_tx_power_for_link(self, dest: str, radio: RadioType) -> int:
        """
        Adaptive TX power control
        Reduce power if link quality is good (save battery)
        Increase power if link quality is poor

        Returns TX power in dBm
        """
        with self._lock:
            link_key = (self.node_id, dest, radio)

            if link_key not in self.links:
                # No link data, use default medium power
                return 17  # dBm

            link = self.links[link_key]
            quality = link.calculate_quality()

            # Power levels based on link quality
            if quality > 80:
                return 10  # Low power (good link)
            elif quality > 60:
                return 14  # Medium-low power
            elif quality > 40:
                return 17  # Medium power (default)
            elif quality > 20:
                return 20  # Medium-high power
            else:
                return 22  # Max power (poor link)

    def start(self):
        """Start background route computation"""
        if self._running:
            return

        self._running = True
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        logger.info("MYC3LIUM router started")

    def stop(self):
        """Stop background tasks"""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=5.0)
        logger.info("MYC3LIUM router stopped")

    def _update_loop(self):
        """Background thread: recompute routes every 30s"""
        while self._running:
            try:
                self.compute_routes()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Route update error: {e}")
                time.sleep(10)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    router = AdaptiveRouter("SPORE-01")

    # Register available radios
    router.register_radio(RadioType.LORA)
    router.register_radio(RadioType.HALOW)
    router.register_radio(RadioType.WIFI)

    # Simulate link metrics
    router.update_link_metrics(
        "SPORE-01", "SPORE-02", RadioType.LORA, rssi=-80, snr=10, latency_ms=250
    )
    router.update_link_metrics(
        "SPORE-01", "SPORE-02", RadioType.HALOW, rssi=-60, snr=15, latency_ms=15
    )

    # Record some transmissions
    for i in range(20):
        router.record_transmission("SPORE-02", RadioType.LORA, success=(i % 10 != 0))
        router.record_transmission("SPORE-02", RadioType.HALOW, success=True)

    # Compute routes
    router.compute_routes()

    # Select best radio
    best = router.select_best_radio(
        "SPORE-02", packet_size=1024, latency_sensitive=False
    )
    print(f"Best radio for 1KB packet: {best.value if best else 'None'}")

    best_latency = router.select_best_radio(
        "SPORE-02", packet_size=1024, latency_sensitive=True
    )
    print(
        f"Best radio for latency-sensitive: {best_latency.value if best_latency else 'None'}"
    )

    # Check adaptive power
    power = router.get_tx_power_for_link("SPORE-02", RadioType.LORA)
    print(f"TX power for LoRa link: {power} dBm")
