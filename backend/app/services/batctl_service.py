"""
BATMAN-adv mesh data via batctl CLI.
Falls back to None/empty on systems without batctl (e.g., Mac dev environments).

Example batctl output:

$ batctl meshif bat0 originators
[B.A.T.M.A.N. adv 2023.2, MainIF/MAC: wlan0/aa:bb:cc:dd:ee:ff (bat0/11:22:33:44:55:66 BATMAN_IV)]
  Originator        last-seen (#/255)          Nexthop     outgoingIF
       aa:bb:cc:dd:ee:01    0.150s   (255) aa:bb:cc:dd:ee:01         wlan0
       aa:bb:cc:dd:ee:02    0.320s   (234) aa:bb:cc:dd:ee:02         wlan0
  *    aa:bb:cc:dd:ee:03    1.240s   (198) aa:bb:cc:dd:ee:01         wlan0

$ batctl meshif bat0 neighbors
[B.A.T.M.A.N. adv 2023.2, MainIF/MAC: wlan0/aa:bb:cc:dd:ee:ff (bat0 BATMAN_IV)]
IF             Neighbor             last-seen
wlan0  aa:bb:cc:dd:ee:01    0.160s ( 255)
wlan0  aa:bb:cc:dd:ee:02    0.430s ( 234)
"""

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional, Union

logger = logging.getLogger(__name__)

BATCTL = shutil.which("batctl")
MESHIF = "bat0"
BATCTL_TIMEOUT_SECONDS = 10

# Security: Interface name validation pattern to prevent path traversal
VALID_IFACE_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class Originator:
    """BATMAN originator (node in the mesh)"""

    mac: str
    last_seen: float  # seconds
    next_hop: str
    interface: str
    tq: int  # transmission quality (0-255)


@dataclass
class Neighbor:
    """Direct neighbor visible on a local interface"""

    mac: str
    last_seen: float  # seconds
    tq: int  # transmission quality (0-255)
    interface: str


@dataclass
class InterfaceStats:
    """Network interface statistics from /sys/class/net/"""

    name: str
    is_up: bool
    tx_bytes: int
    rx_bytes: int
    tx_packets: int
    rx_packets: int


def is_available() -> bool:
    """
    Check if batctl is installed and bat0 interface exists.

    Returns:
        True if batctl is available and responding, False otherwise
    """
    if not BATCTL:
        logger.debug("batctl not found in PATH")
        return False

    try:
        result = subprocess.run(
            [BATCTL, "meshif", MESHIF, "interface"],
            capture_output=True,
            text=True,
            timeout=BATCTL_TIMEOUT_SECONDS,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("batctl availability check failed: %s", e)
        return False


def get_originators() -> Optional[list[Originator]]:
    """
    Parse `batctl meshif bat0 originators` output.

    Returns:
        List of Originator objects, or None if batctl unavailable or parse fails
    """
    if not BATCTL:
        return None

    try:
        result = subprocess.run(
            [BATCTL, "meshif", MESHIF, "originators"],
            capture_output=True,
            text=True,
            timeout=BATCTL_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning(
                "batctl originators failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return None

        nodes = []
        for line in result.stdout.splitlines():
            # Security: Skip overly long lines to prevent ReDoS (H-2)
            if len(line) > 512:
                continue

            # Match lines like:
            #   *    aa:bb:cc:dd:ee:03    1.240s   (198) aa:bb:cc:dd:ee:01         wlan0
            #        aa:bb:cc:dd:ee:01    0.150s   (255) aa:bb:cc:dd:ee:01         wlan0
            # Security: Use bounded quantifiers to prevent catastrophic backtracking (H-2)
            match = re.match(
                r"^\s{0,10}\*?\s{0,10}([\da-f:]{17})\s{1,10}([\d.]{1,10})s\s{1,10}\(\s{0,5}(\d{1,3})\)\s{1,10}([\da-f:]{17})\s{1,10}(\S+)",
                line,
            )
            if match:
                nodes.append(
                    Originator(
                        mac=match.group(1),
                        last_seen=float(match.group(2)),
                        tq=int(match.group(3)),
                        next_hop=match.group(4),
                        interface=match.group(5),
                    )
                )

        logger.debug("Parsed %d originators from batctl", len(nodes))
        return nodes

    except subprocess.TimeoutExpired:
        logger.error("batctl originators timed out after %ds", BATCTL_TIMEOUT_SECONDS)
        return None
    except (FileNotFoundError, ValueError, IndexError) as e:
        logger.error("batctl originators parse error: %s", e)
        return None


def get_neighbors() -> Optional[list[Neighbor]]:
    """
    Parse `batctl meshif bat0 neighbors` output.

    Returns:
        List of Neighbor objects, or None if batctl unavailable or parse fails
    """
    if not BATCTL:
        return None

    try:
        result = subprocess.run(
            [BATCTL, "meshif", MESHIF, "neighbors"],
            capture_output=True,
            text=True,
            timeout=BATCTL_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning(
                "batctl neighbors failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return None

        neighbors = []
        for line in result.stdout.splitlines():
            # Security: Skip overly long lines to prevent ReDoS (H-2)
            if len(line) > 512:
                continue

            # Match lines like:
            # wlan0  aa:bb:cc:dd:ee:01    0.160s ( 255)
            # Security: Use bounded quantifiers to prevent catastrophic backtracking (H-2)
            match = re.match(
                r"^(\S{1,20})\s{1,10}([\da-f:]{17})\s{1,10}([\d.]{1,10})s\s{1,10}\(\s{0,5}(\d{1,3})\)",
                line,
            )
            if match:
                neighbors.append(
                    Neighbor(
                        interface=match.group(1),
                        mac=match.group(2),
                        last_seen=float(match.group(3)),
                        tq=int(match.group(4)),
                    )
                )

        logger.debug("Parsed %d neighbors from batctl", len(neighbors))
        return neighbors

    except subprocess.TimeoutExpired:
        logger.error("batctl neighbors timed out after %ds", BATCTL_TIMEOUT_SECONDS)
        return None
    except (FileNotFoundError, ValueError, IndexError) as e:
        logger.error("batctl neighbors parse error: %s", e)
        return None


def get_interface_stats(interface: str) -> Optional[InterfaceStats]:
    """
    Get interface statistics from /sys/class/net/<interface>/statistics/.

    Args:
        interface: Network interface name (e.g., 'wlan0', 'bat0')

    Returns:
        InterfaceStats object, or None if interface doesn't exist or read fails
    """
    import os

    # Security: Validate interface name to prevent path traversal (H-1)
    if not VALID_IFACE_PATTERN.match(interface):
        logger.warning("Invalid interface name: %s", interface)
        return None

    sys_path = f"/sys/class/net/{interface}"
    if not os.path.exists(sys_path):
        logger.debug("Interface %s not found at %s", interface, sys_path)
        return None

    try:

        def read_int(path: str, default: int = 0) -> int:
            """Read integer from sysfs file, return default if error"""
            try:
                with open(path, encoding="utf-8") as f:
                    return int(f.read().strip())
            except (FileNotFoundError, ValueError, PermissionError):
                return default

        # Check operstate to determine if interface is up
        operstate_path = f"{sys_path}/operstate"
        operstate = "unknown"
        if os.path.exists(operstate_path):
            with open(operstate_path, encoding="utf-8") as f:
                operstate = f.read().strip()

        is_up = operstate in ("up", "unknown")

        return InterfaceStats(
            name=interface,
            is_up=is_up,
            tx_bytes=read_int(f"{sys_path}/statistics/tx_bytes"),
            rx_bytes=read_int(f"{sys_path}/statistics/rx_bytes"),
            tx_packets=read_int(f"{sys_path}/statistics/tx_packets"),
            rx_packets=read_int(f"{sys_path}/statistics/rx_packets"),
        )

    except (FileNotFoundError, ValueError, PermissionError) as e:
        logger.error("Failed to read interface stats for %s: %s", interface, e)
        return None


def get_statistics() -> Optional[dict[str, Union[int, str]]]:
    """
    Parse `batctl meshif bat0 statistics` output.

    Returns:
        Dictionary of statistics, or None if batctl unavailable
    """
    if not BATCTL:
        return None

    try:
        result = subprocess.run(
            [BATCTL, "meshif", MESHIF, "statistics"],
            capture_output=True,
            text=True,
            timeout=BATCTL_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning(
                "batctl statistics failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return None

        stats: dict[str, Union[int, str]] = {}
        for line in result.stdout.splitlines():
            # Parse lines like "mgmt_tx: 1234" or "mgmt_tx_bytes: 567890"
            parts = line.strip().split(":")
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(" ", "_")
                val = parts[1].strip()
                try:
                    stats[key] = int(val)
                except ValueError:
                    stats[key] = val

        logger.debug("Parsed %d statistics from batctl", len(stats))
        return stats

    except subprocess.TimeoutExpired:
        logger.error("batctl statistics timed out after %ds", BATCTL_TIMEOUT_SECONDS)
        return None
    except (FileNotFoundError, ValueError) as e:
        logger.error("batctl statistics parse error: %s", e)
        return None
