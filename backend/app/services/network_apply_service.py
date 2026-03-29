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

from app.config_models import MeshConfig, Myc3liumConfig

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


def apply_batman(mesh_config: MeshConfig) -> dict[str, Any]:
    """Apply BATMAN-adv mesh settings to running system.

    - Joins mesh with configured SSID
    - Sets channel/frequency for band

    Returns:
        Dict with 'success', 'message', and 'details' keys
    """
    if not _IS_LINUX:
        return {
            "success": False,
            "message": "BATMAN apply only available on Linux (Pi)",
            "details": [],
        }

    details: list[str] = []
    errors: list[str] = []

    # Leave current mesh (if any) before rejoining
    _run(["sudo", "iw", "dev", "wlan0", "mesh", "leave"])

    # Set frequency
    freq = _channel_to_freq(mesh_config.batman_channel, mesh_config.batman_band)
    if freq:
        result = _run(["sudo", "iw", "dev", "wlan0", "set", "freq", str(freq)])
        if result.returncode == 0:
            details.append(
                f"Set wlan0 frequency to {freq} MHz (ch {mesh_config.batman_channel})"
            )
        else:
            errors.append(f"Failed to set frequency: {result.stderr.strip()}")

    # Join mesh
    result = _run(
        [
            "sudo",
            "iw",
            "dev",
            "wlan0",
            "mesh",
            "join",
            mesh_config.batman_ssid,
            "freq",
            str(freq or 2437),
        ]
    )
    if result.returncode == 0:
        details.append(f"Joined mesh '{mesh_config.batman_ssid}'")
    else:
        errors.append(f"Failed to join mesh: {result.stderr.strip()}")

    # Restart BATMAN service
    result = _run(["sudo", "systemctl", "restart", "batman-adv"])
    if result.returncode == 0:
        details.append("Restarted batman-adv service")
    else:
        # batman-adv may not be a service, try modprobe
        modprobe_result = _run(["sudo", "modprobe", "batman-adv"])
        if modprobe_result.returncode == 0:
            details.append("Loaded batman-adv kernel module")
        else:
            errors.append(f"batman-adv not available: {modprobe_result.stderr.strip()}")

    success = len(errors) == 0
    message = (
        "BATMAN config applied" if success else f"BATMAN errors: {'; '.join(errors)}"
    )

    logger.info(
        "apply_batman: success=%s details=%s errors=%s", success, details, errors
    )
    return {"success": success, "message": message, "details": details + errors}


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
