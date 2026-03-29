"""
Backhaul / AP mode service for MYC3LIUM.

Manages USB WiFi adapter detection, client mode (internet backhaul),
AP mode (myc3_m3sh hotspot), NAT, and mesh bridging.

AP clients are bridged into the BATMAN mesh via a Linux bridge (br0):
  AP clients -> wlan1 (hostapd, bridge=br0) -> br0 <- bat0 (BATMAN mesh)

System-level operations (iptables, hostapd, bridge) are performed via
the myc3lium-netctl privileged helper script, which the backend calls
via sudo. This keeps the systemd service sandboxed while allowing
controlled network operations.

On macOS, returns mock/no-op results for development.
"""

from __future__ import annotations

import logging
import platform
import subprocess
from pathlib import Path
from typing import Any

from app.config_models import BackhaulConfig

logger = logging.getLogger(__name__)

# Config file paths on Pi (written via netctl helper)
HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")
DNSMASQ_CONF = Path("/etc/dnsmasq.d/myc3lium-ap.conf")

# Internal mesh interface — never use for backhaul
MESH_INTERFACE = "wlan0"

# State file — writable by myc3lium app user
_STATE_DIR = Path("/opt/myc3lium/run")
_STATE_FILE = _STATE_DIR / "backhaul-iface"

# Bridge interface for connecting AP clients to BATMAN mesh
BRIDGE_INTERFACE = "br0"

# Privileged helper script
NETCTL = "myc3lium-netctl"

_IS_LINUX = platform.system() == "Linux"


def _run(cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    """Run a shell command, capturing output. Returns rc=1 on timeout."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out after %ds: %s", timeout, cmd)
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr="timeout"
        )


def _netctl(
    command: str, *args: str, stdin: str | None = None, timeout: int = 15
) -> subprocess.CompletedProcess[str]:
    """Call the myc3lium-netctl privileged helper via sudo."""
    cmd = ["sudo", NETCTL, command, *args]
    try:
        return subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.warning("netctl %s timed out after %ds", command, timeout)
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr="timeout"
        )


def _save_active_interface(interface: str) -> None:
    """Record which interface is being used for backhaul."""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(interface)
    except OSError as e:
        logger.warning("Could not write state file: %s", e)


def _read_active_interface() -> str | None:
    """Read the previously active backhaul interface."""
    try:
        if _STATE_FILE.exists():
            return _STATE_FILE.read_text().strip() or None
    except OSError:
        pass
    return None


def detect_usb_wifi_adapters() -> list[dict[str, str]]:
    """Scan for USB-backed wireless interfaces, excluding wlan0 (mesh).

    Returns:
        List of dicts with keys: name, driver, mac, usb_id
    """
    if not _IS_LINUX:
        return []

    adapters: list[dict[str, str]] = []
    net_path = Path("/sys/class/net")

    for iface_path in net_path.iterdir():
        try:
            name = iface_path.name
            if name == MESH_INTERFACE:
                continue

            wireless_path = iface_path / "wireless"
            if not wireless_path.exists():
                continue

            device_link = iface_path / "device"
            if not device_link.exists():
                continue

            real_path = device_link.resolve()
            if "/usb" not in str(real_path):
                continue

            mac = ""
            mac_path = iface_path / "address"
            if mac_path.exists():
                mac = mac_path.read_text().strip()

            driver = ""
            driver_link = device_link / "driver"
            if driver_link.exists():
                driver = driver_link.resolve().name

            usb_id = ""
            try:
                usb_device = real_path.parent
                vendor = (usb_device / "idVendor").read_text().strip()
                product = (usb_device / "idProduct").read_text().strip()
                usb_id = f"{vendor}:{product}"
            except (FileNotFoundError, OSError):
                pass

            adapters.append(
                {
                    "name": name,
                    "driver": driver,
                    "mac": mac,
                    "usb_id": usb_id,
                }
            )
        except (OSError, FileNotFoundError):
            continue

    logger.info("Detected %d USB WiFi adapter(s): %s", len(adapters), adapters)
    return adapters


def get_available_interface() -> str | None:
    """Return the first non-mesh USB WiFi adapter name, or None."""
    adapters = detect_usb_wifi_adapters()
    return adapters[0]["name"] if adapters else None


def apply_client_mode(config: BackhaulConfig) -> tuple[bool, str, str | None]:
    """Configure USB WiFi adapter as a client to join an existing network.

    Uses wpa_passphrase to hash the PSK rather than storing plaintext.

    Returns:
        Tuple of (success, message, interface_used)
    """
    if not _IS_LINUX:
        return False, "Client mode only available on Linux (Pi)", None

    interface = config.interface or get_available_interface()
    if not interface:
        return False, "No USB WiFi adapter detected", None

    # Use wpa_passphrase to generate hashed PSK
    wpa_gen = _run(
        ["wpa_passphrase", config.client_ssid, config.client_password], timeout=5
    )
    if wpa_gen.returncode == 0:
        wpa_config = (
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n"
            "update_config=1\n\n"
        ) + wpa_gen.stdout
    else:
        logger.warning("wpa_passphrase failed, using plaintext PSK")
        wpa_config = (
            "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n"
            "update_config=1\n\n"
            "network={\n"
            f'    ssid="{config.client_ssid}"\n'
            f'    psk="{config.client_password}"\n'
            "    key_mgmt=WPA-PSK\n"
            "}\n"
        )

    # Write config via privileged helper
    result = _netctl("write-wpa", stdin=wpa_config)
    if result.returncode != 0:
        logger.error("Failed to write wpa_supplicant config: %s", result.stderr)
        return False, "Failed to write wpa_supplicant config", None

    # Stop AP services if switching modes
    _netctl("stop-ap")

    # Start client mode
    result = _netctl("start-client", interface, timeout=30)
    if result.returncode != 0:
        logger.error("Client mode failed on %s: %s", interface, result.stderr)
        return False, f"Failed to connect on {interface}", interface

    _save_active_interface(interface)
    logger.info(
        "Client mode active on %s, connected to %s", interface, config.client_ssid
    )
    return True, f"Connected to {config.client_ssid} on {interface}", interface


def apply_ap_mode(config: BackhaulConfig) -> tuple[bool, str, str | None]:
    """Configure USB WiFi adapter as an access point.

    Creates a Linux bridge (br0) connecting AP clients to BATMAN mesh.

    Returns:
        Tuple of (success, message, interface_used)
    """
    if not _IS_LINUX:
        return False, "AP mode only available on Linux (Pi)", None

    interface = config.interface or get_available_interface()
    if not interface:
        return False, "No USB WiFi adapter detected", None

    # Set up br0 bridge with bat0
    _netctl("setup-bridge")

    # Build hostapd config
    if config.ap_band == "5GHz":
        hw_mode = "a"
        extra = "ieee80211n=1\nieee80211ac=1\n"
    else:
        hw_mode = "g"
        extra = "ieee80211n=1\n"

    hostapd_config = (
        f"interface={interface}\n"
        f"bridge={BRIDGE_INTERFACE}\n"
        f"ssid={config.ap_ssid}\n"
        f"hw_mode={hw_mode}\n"
        f"channel={config.ap_channel}\n"
        f"wpa=2\n"
        f"wpa_passphrase={config.ap_password}\n"
        f"wpa_key_mgmt=WPA-PSK\n"
        f"rsn_pairwise=CCMP\n"
        f"ignore_broadcast_ssid={'1' if config.ap_hidden else '0'}\n"
        f"{extra}"
        f"wmm_enabled=0\n"
        f"country_code=US\n"
    )

    # Get hostname for local DNS resolution (myc3.local -> AP IP)
    hostname = "myc3"
    try:
        import socket

        hostname = socket.gethostname()
    except OSError:
        pass

    dnsmasq_config = (
        f"interface={BRIDGE_INTERFACE}\n"
        f"bind-dynamic\n"
        f"dhcp-range=10.99.0.10,10.99.0.200,255.255.255.0,24h\n"
        f"dhcp-option=3,10.99.0.1\n"
        f"dhcp-option=6,10.99.0.1\n"
        f"server=8.8.8.8\n"
        f"server=1.1.1.1\n"
        f"address=/{hostname}.local/10.99.0.1\n"
    )

    # Write configs via privileged helper
    result = _netctl("write-hostapd", stdin=hostapd_config)
    if result.returncode != 0:
        logger.error("Failed to write hostapd config: %s", result.stderr)
        return False, "Failed to write hostapd config", None

    result = _netctl("write-dnsmasq", stdin=dnsmasq_config)
    if result.returncode != 0:
        logger.error("Failed to write dnsmasq config: %s", result.stderr)
        return False, "Failed to write dnsmasq config", None

    # Stop client mode if switching
    _netctl("stop-client", interface)

    # Set static IP on bridge
    _netctl("set-ip", BRIDGE_INTERFACE, "10.99.0.1/24")
    _netctl("iface-up", interface)

    # Start hostapd and dnsmasq
    result = _netctl("start-ap")
    if result.returncode != 0:
        logger.error("AP start failed: %s", result.stderr)
        return False, "AP failed to start (check system logs)", interface

    _save_active_interface(interface)
    logger.info(
        "AP mode active on %s: SSID=%s, bridge=%s",
        interface,
        config.ap_ssid,
        BRIDGE_INTERFACE,
    )
    return True, f"AP '{config.ap_ssid}' active on {interface}", interface


def _get_default_route_interface() -> str | None:
    """Get the interface used for the default route (internet uplink)."""
    result = _run(["ip", "route", "show", "default"])
    if result.returncode == 0 and result.stdout.strip():
        # "default via 192.168.40.1 dev wlan0 ..."
        parts = result.stdout.strip().split()
        if "dev" in parts:
            return parts[parts.index("dev") + 1]
    return None


def apply_nat(backhaul_interface: str) -> tuple[bool, str]:
    """Enable NAT/masquerade from AP/mesh bridge out through the internet interface.

    In AP mode, the backhaul_interface is the AP itself — NAT must go through
    the default route interface (e.g., wlan0 on home network), not the AP.

    In client mode, the backhaul_interface IS the internet uplink, so NAT
    goes through it directly.
    """
    if not _IS_LINUX:
        return False, "NAT only available on Linux (Pi)"

    # Determine the actual internet-facing interface
    default_iface = _get_default_route_interface()

    # In AP mode: NAT through default route (wlan0), not the AP (wlan1)
    # In client mode: the backhaul interface IS the default route
    if default_iface and default_iface != backhaul_interface:
        nat_out = default_iface
    else:
        nat_out = backhaul_interface

    result = _netctl("setup-nat", nat_out)
    if result.returncode != 0:
        logger.error("NAT setup failed: %s", result.stderr)
        return False, "NAT setup failed (check system logs)"

    logger.info("NAT enabled: br0 -> %s", nat_out)
    return True, f"NAT active: br0 -> {nat_out}"


def remove_nat_rules(interface: str) -> None:
    """Remove myc3lium NAT rules for a specific interface.

    Also tries the default route interface in case NAT was set up
    through a different interface than the one being removed.
    """
    _netctl("remove-nat", interface)
    # Also clean up NAT through the default route interface
    default_iface = _get_default_route_interface()
    if default_iface and default_iface != interface:
        _netctl("remove-nat", default_iface)


def disable_backhaul() -> tuple[bool, str]:
    """Stop all backhaul services and clean up."""
    if not _IS_LINUX:
        return False, "Backhaul management only available on Linux (Pi)"

    interface = _read_active_interface()

    if not interface:
        # Try to find from hostapd config
        if HOSTAPD_CONF.exists():
            try:
                for line in HOSTAPD_CONF.read_text().splitlines():
                    if line.startswith("interface="):
                        interface = line.split("=", 1)[1].strip()
                        break
            except OSError:
                pass

    # Full cleanup via privileged helper
    if interface:
        _netctl("cleanup", interface)
    else:
        _netctl("cleanup")

    # Clean up state file
    try:
        _STATE_FILE.unlink(missing_ok=True)
    except OSError:
        pass

    logger.info("Backhaul disabled, all services stopped")
    return True, "Backhaul disabled"


def get_status(config: BackhaulConfig | None = None) -> dict[str, Any]:
    """Get current backhaul status including adapters, mode, IP, clients.

    Args:
        config: BackhaulConfig from TOML, used for SSID when hostapd.conf
                is not readable by the service user.
    """
    adapters = detect_usb_wifi_adapters()

    status: dict[str, Any] = {
        "adapters": adapters,
        "active_interface": None,
        "mode": "disabled",
        "ip_address": None,
        "connected_clients": 0,
        "ssid": None,
        "signal": None,
    }

    if not _IS_LINUX or not adapters:
        return status

    # Check if hostapd is running (AP mode)
    hostapd_check = _run(["systemctl", "is-active", "hostapd"])
    if hostapd_check.stdout.strip() == "active":
        status["mode"] = "ap"

        # SSID from config (hostapd.conf is root-only 600)
        if config:
            status["ssid"] = config.ap_ssid

        interface = _read_active_interface() or adapters[0]["name"]
        status["active_interface"] = interface

        # Count connected clients via hostapd_cli (/usr/sbin, not in regular PATH)
        clients_result = _run(["/usr/sbin/hostapd_cli", "-i", interface, "all_sta"])
        if clients_result.returncode == 0:
            macs = [
                line
                for line in clients_result.stdout.splitlines()
                if len(line) == 17 and line.count(":") == 5
            ]
            status["connected_clients"] = len(macs)

        # Get IP from bridge
        ip_result = _run(["ip", "-4", "addr", "show", BRIDGE_INTERFACE])
        if ip_result.returncode == 0:
            for line in ip_result.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    status["ip_address"] = line.split()[1].split("/")[0]
                    break

        return status

    # Check if wpa_supplicant is running (client mode)
    wpa_check = _run(["pgrep", "-f", "wpa_supplicant.*backhaul"])
    if wpa_check.returncode == 0 and adapters:
        status["mode"] = "client"
        interface = _read_active_interface() or adapters[0]["name"]
        status["active_interface"] = interface

        # Try to get live SSID from iw, fall back to config
        iw_result = _run(["iw", "dev", interface, "link"])
        if iw_result.returncode == 0:
            for line in iw_result.stdout.splitlines():
                line = line.strip()
                if line.startswith("SSID:"):
                    status["ssid"] = line.split(":", 1)[1].strip()
                elif line.startswith("signal:"):
                    status["signal"] = line.split(":", 1)[1].strip()

        if not status["ssid"] and config:
            status["ssid"] = config.client_ssid

        ip_result = _run(["ip", "-4", "addr", "show", interface])
        if ip_result.returncode == 0:
            for line in ip_result.stdout.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    status["ip_address"] = line.split()[1].split("/")[0]
                    break

    return status
