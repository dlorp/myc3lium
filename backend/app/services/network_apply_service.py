"""
Network apply service for MYC3LIUM.

Wires P600 config changes to running system services:
- BATMAN-adv: mesh join, channel/frequency
- Reticulum: transport, store-forward, LoRa interface params
- Meshtastic: start/stop based on config
"""

from __future__ import annotations

import logging
import platform
import subprocess
from pathlib import Path
from typing import Any

from app.config_models import HaLowConfig, MeshConfig, Myc3liumConfig

logger = logging.getLogger(__name__)

_IS_LINUX = platform.system() == "Linux"

# Reticulum config location on Pi
RETICULUM_CONF = Path("/opt/myc3lium/config/reticulum.conf")
RETICULUM_CONF_DEV = Path("./reticulum.conf")

# Channel-to-frequency mappings
_FREQ_2_4GHZ: dict[int, int] = {
    1: 2412,
    2: 2417,
    3: 2422,
    4: 2427,
    5: 2432,
    6: 2437,
    7: 2442,
    8: 2447,
    9: 2452,
    10: 2457,
    11: 2462,
}

_FREQ_5GHZ: dict[int, int] = {
    36: 5180,
    40: 5200,
    44: 5220,
    48: 5240,
    52: 5260,
    56: 5280,
    60: 5300,
    64: 5320,
    100: 5500,
    104: 5520,
    108: 5540,
    112: 5560,
    116: 5580,
    120: 5600,
    124: 5620,
    128: 5640,
    132: 5660,
    136: 5680,
    140: 5700,
    144: 5720,
    149: 5745,
    153: 5765,
    157: 5785,
    161: 5805,
    165: 5825,
}


def _run(cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    """Run a shell command, capturing output. Returns rc=1 on timeout."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out after %ds: %s", timeout, cmd)
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr="timeout"
        )


def _channel_to_freq(channel: int, band: str) -> int | None:
    """Convert WiFi channel + band to frequency in MHz."""
    if band == "2.4GHz":
        return _FREQ_2_4GHZ.get(channel)
    return _FREQ_5GHZ.get(channel)


def _netctl(
    command: str, *args: str, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    """Call myc3lium-netctl privileged helper via sudo."""
    cmd = ["sudo", "myc3lium-netctl", command, *args]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning("netctl %s timed out after %ds", command, timeout)
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr="timeout"
        )


def _derive_mesh_ip(interface: str = "wlan0") -> str | None:
    """Derive a deterministic mesh IP from the MAC address of an interface.

    Uses last two octets of MAC -> 10.13.<octet5>.<octet6>/16.
    Avoids .0 and .255 for the host octet.
    Returns None if MAC cannot be read (caller should abort).
    """
    import re

    if not re.match(r"^[a-zA-Z0-9]{1,15}$", interface):
        logger.error("Invalid interface name for mesh IP derivation: %s", interface)
        return None
    # Read without resolve() — sysfs symlinks resolve to /sys/devices/...
    # which breaks is_relative_to checks. The regex above prevents traversal.
    mac_path = Path(f"/sys/class/net/{interface}/address")
    try:
        mac = mac_path.read_text().strip()  # e.g. "dc:a6:32:xx:ab:2a"
        parts = mac.split(":")
        if len(parts) != 6:
            logger.error("Malformed MAC address for %s: %s", interface, mac)
            return None
        octet5 = int(parts[4], 16)
        octet6 = int(parts[5], 16)
        if octet6 == 0:
            octet6 = 1
        elif octet6 == 255:
            octet6 = 254
        return f"10.13.{octet5}.{octet6}/16"
    except (OSError, IndexError, ValueError) as exc:
        logger.error("Failed to read MAC from %s: %s", interface, exc)
        return None


def apply_batman(mesh_config: MeshConfig) -> dict[str, Any]:
    """Apply BATMAN-adv mesh over IBSS on wlan0.

    Calls myc3lium-netctl mesh-up which handles:
    - Loading batman-adv kernel module
    - Unmanaging wlan0 from NetworkManager
    - Setting wlan0 to IBSS mode with correct MTU
    - Joining the IBSS cell at configured frequency
    - Creating bat0 and adding wlan0
    - Assigning deterministic mesh IP to bat0

    Returns:
        Dict with 'success', 'message', and 'details' keys.
    """
    if not _IS_LINUX:
        return {
            "success": False,
            "message": "BATMAN apply only available on Linux (Pi)",
            "details": [],
        }

    details: list[str] = []

    freq = _channel_to_freq(mesh_config.batman_channel, mesh_config.batman_band)
    if not freq:
        return {
            "success": False,
            "message": (
                f"Invalid channel {mesh_config.batman_channel} "
                f"for {mesh_config.batman_band}"
            ),
            "details": [],
        }

    mesh_ip = _derive_mesh_ip("wlan0")
    if not mesh_ip:
        return {
            "success": False,
            "message": "Could not derive mesh IP from wlan0 MAC",
            "details": [],
        }
    details.append(f"Mesh IP: {mesh_ip}")

    result = _netctl("mesh-up", mesh_config.batman_ssid, str(freq), mesh_ip)

    if result.returncode == 0:
        details.append(
            f"IBSS joined: {mesh_config.batman_ssid} @ {freq} MHz "
            f"(ch {mesh_config.batman_channel})"
        )
        details.append(f"bat0 up with IP {mesh_ip}")
        logger.info("apply_batman: success, details=%s", details)
        return {"success": True, "message": "BATMAN mesh active", "details": details}

    error = result.stderr.strip() or result.stdout.strip()
    logger.error("apply_batman: mesh-up failed: %s", error)
    return {
        "success": False,
        "message": f"BATMAN mesh-up failed: {error}",
        "details": details + [f"Error: {error}"],
    }


def teardown_batman() -> dict[str, Any]:
    """Tear down BATMAN-adv mesh cleanly."""
    if not _IS_LINUX:
        return {"success": True, "message": "Not on Linux", "details": []}
    result = _netctl("mesh-down")
    success = result.returncode == 0
    msg = "BATMAN mesh torn down" if success else result.stderr.strip()
    if success:
        logger.info("BATMAN mesh torn down")
    else:
        logger.warning("BATMAN mesh-down failed: %s", msg)
    return {"success": success, "message": msg, "details": []}


def apply_halow(halow_config: HaLowConfig) -> dict[str, Any]:
    """Add or remove HaLow interface as a BATMAN transport on bat0.

    Calls myc3lium-netctl halow-up/halow-down which handles:
    - Auto-detecting usb0 (USB-ECM) or halow0 (TAP/SLIP bridge)
    - Adding/removing the interface from bat0
    - Setting MTU to 1560 for BATMAN overhead headroom

    Returns:
        Dict with 'success', 'message', and 'details' keys.
    """
    if not _IS_LINUX:
        return {
            "success": False,
            "message": "HaLow apply only available on Linux (Pi)",
            "details": [],
        }

    if not halow_config.enabled:
        result = _netctl("halow-down")
        success = result.returncode == 0
        msg = "HaLow transport removed from bat0" if success else result.stderr.strip()
        logger.info("apply_halow: disabled, halow-down result=%s", msg)
        return {"success": success, "message": msg, "details": []}

    # Determine interface to pass (empty = auto-detect in netctl)
    iface_arg = halow_config.interface or ""
    args = ["halow-up"]
    if iface_arg:
        args.append(iface_arg)

    result = _netctl(*args)

    if result.returncode == 0:
        output = result.stdout.strip()
        logger.info("apply_halow: success: %s", output)
        return {
            "success": True,
            "message": "HaLow transport active on bat0",
            "details": [output],
        }

    error = result.stderr.strip() or result.stdout.strip()
    logger.error("apply_halow: halow-up failed: %s", error)
    return {
        "success": False,
        "message": f"HaLow halow-up failed: {error}",
        "details": [f"Error: {error}"],
    }


def halow_status() -> dict[str, Any]:
    """Get current HaLow interface status."""
    if not _IS_LINUX:
        return {"status": "unavailable", "interface": "none"}

    result = _netctl("halow-status")
    if result.returncode == 0:
        # Parse "halow=active interface=halow0"
        output = result.stdout.strip()
        parts = dict(item.split("=", 1) for item in output.split() if "=" in item)
        return {
            "status": parts.get("halow", "unknown"),
            "interface": parts.get("interface", "none"),
        }
    return {"status": "error", "interface": "none"}


def apply_reticulum(config: Myc3liumConfig) -> dict[str, Any]:
    """Apply Reticulum settings to reticulum.conf and restart service.

    Maps config fields to Reticulum config sections:
    - reticulum_transport -> enable_transport
    - store_forward_enabled/max -> storage section
    - LoRa radio params -> interface section
    """
    conf_path = RETICULUM_CONF if _IS_LINUX else RETICULUM_CONF_DEV
    mesh = config.mesh
    radio = config.radio

    # Build Reticulum config (ConfigObj format, not TOML)
    conf_lines = [
        "[reticulum]",
        f"  enable_transport = {'True' if mesh.reticulum_transport else 'False'}",
        "",
        "[storage]",
        f"  enabled = {'True' if mesh.store_forward_enabled else 'False'}",
        f"  max_messages = {mesh.store_forward_max_messages}",
        "",
        "[interfaces]",
        "",
        "  [[RNodeInterface]]",
        "    type = RNodeInterface",
        "    interface_enabled = True",
        f"    port = {radio.meshtastic_device}",
        f"    frequency = {radio.lora_frequency}",
        f"    bandwidth = {radio.lora_bandwidth}",
        f"    spreading_factor = {radio.lora_spreading_factor}",
        f"    txpower = {radio.lora_tx_power}",
        "",
    ]

    try:
        conf_path.parent.mkdir(parents=True, exist_ok=True)
        conf_path.write_text("\n".join(conf_lines))
        logger.info("Wrote Reticulum config to %s", conf_path)
    except OSError as e:
        return {
            "success": False,
            "message": f"Failed to write reticulum.conf: {e}",
            "details": [],
        }

    details = [f"Wrote {conf_path}"]

    # Restart Reticulum service on Linux
    if _IS_LINUX:
        result = _run(["sudo", "systemctl", "restart", "reticulum"])
        if result.returncode == 0:
            details.append("Restarted reticulum service")
        else:
            return {
                "success": False,
                "message": f"Failed to restart reticulum: {result.stderr.strip()}",
                "details": details,
            }

    return {"success": True, "message": "Reticulum config applied", "details": details}


def apply_meshtastic(config: Myc3liumConfig) -> dict[str, Any]:
    """Apply Meshtastic settings — start or stop based on config.

    The actual serial device and enabled flag come from RadioConfig.
    """
    radio = config.radio
    details: list[str] = []

    if not radio.meshtastic_enabled:
        if _IS_LINUX:
            _run(["sudo", "systemctl", "stop", "meshtastic"])
            details.append("Stopped Meshtastic service")
        return {
            "success": True,
            "message": "Meshtastic disabled per config",
            "details": details,
        }

    details.append(f"Meshtastic enabled on {radio.meshtastic_device}")

    if _IS_LINUX:
        result = _run(["sudo", "systemctl", "restart", "meshtastic"])
        if result.returncode == 0:
            details.append("Restarted Meshtastic service")
        else:
            # Meshtastic may not have a systemd unit — that's OK,
            # the app service manages it via MeshtasticService
            details.append("No systemd unit for Meshtastic (managed by app)")

    return {
        "success": True,
        "message": "Meshtastic config applied",
        "details": details,
    }


def apply_network(config: Myc3liumConfig) -> dict[str, Any]:
    """Apply all network config (BATMAN + Reticulum + Meshtastic).

    Returns combined results from all three.
    """
    batman_result = apply_batman(config.mesh)
    reticulum_result = apply_reticulum(config)
    meshtastic_result = apply_meshtastic(config)

    all_success = all(
        [
            batman_result["success"],
            reticulum_result["success"],
            meshtastic_result["success"],
        ]
    )

    return {
        "success": all_success,
        "batman": batman_result,
        "reticulum": reticulum_result,
        "meshtastic": meshtastic_result,
    }
