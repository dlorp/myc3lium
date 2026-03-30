"""
User-facing configuration models for MYC3LIUM.

These define the TOML config file structure at /opt/myc3lium/config/myc3lium.toml.
Separate from app/config.py which handles internal app settings via env vars.
"""

from __future__ import annotations

import re
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RadioConfig(BaseModel):
    """Radio hardware settings."""

    model_config = ConfigDict(extra="forbid")

    lora_frequency: int = Field(
        915000000, description="LoRa frequency in Hz (US ISM: 915000000)"
    )
    lora_bandwidth: int = Field(125000, description="LoRa bandwidth in Hz")
    lora_spreading_factor: int = Field(
        7, ge=7, le=12, description="LoRa spreading factor (7-12)"
    )
    lora_tx_power: int = Field(22, ge=0, le=22, description="LoRa TX power in dBm")
    meshtastic_device: str = Field(
        "/dev/ttyUSB1", description="Meshtastic serial device path"
    )
    meshtastic_enabled: bool = Field(True, description="Enable Meshtastic integration")

    @field_validator("meshtastic_device")
    @classmethod
    def validate_device_path(cls, v: str) -> str:
        if not re.match(r"^/dev/tty(USB|ACM|S|AMA)\d{1,3}$", v):
            raise ValueError(f"Invalid device path: {v}")
        return v


class MeshConfig(BaseModel):
    """Mesh networking settings."""

    model_config = ConfigDict(extra="forbid")

    batman_channel: int = Field(
        6,
        ge=1,
        le=165,
        description="WiFi channel for BATMAN mesh (1-11 for 2.4GHz, 36-165 for 5GHz)",
    )
    batman_band: Literal["2.4GHz", "5GHz"] = Field(
        "2.4GHz", description="WiFi band for BATMAN mesh"
    )
    batman_ssid: str = Field(
        "myc3lium-mesh", max_length=32, description="BATMAN mesh SSID"
    )
    reticulum_transport: bool = Field(
        True, description="Enable Reticulum transport node"
    )
    store_forward_enabled: bool = Field(
        True, description="Enable store-and-forward messaging"
    )
    store_forward_max_messages: int = Field(
        1000, ge=100, le=10000, description="Max stored messages"
    )

    _VALID_5GHZ_CHANNELS: ClassVar[set[int]] = {
        36,
        40,
        44,
        48,
        52,
        56,
        60,
        64,
        100,
        104,
        108,
        112,
        116,
        120,
        124,
        128,
        132,
        136,
        140,
        144,
        149,
        153,
        157,
        161,
        165,
    }

    @model_validator(mode="after")
    def validate_channel_for_band(self) -> MeshConfig:
        if self.batman_band == "2.4GHz" and not (1 <= self.batman_channel <= 11):
            raise ValueError(
                f"Channel {self.batman_channel} invalid for 2.4GHz (must be 1-11)"
            )
        if (
            self.batman_band == "5GHz"
            and self.batman_channel not in self._VALID_5GHZ_CHANNELS
        ):
            raise ValueError(
                f"Channel {self.batman_channel} is not a valid 5GHz channel"
            )
        return self

    @field_validator("batman_ssid")
    @classmethod
    def validate_ssid(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_-]{1,32}$", v):
            raise ValueError("SSID must be alphanumeric, hyphens, or underscores")
        return v


# Default AP credentials for first-boot auto-AP mode.
# User is expected to change these via the Setup wizard.
BACKHAUL_DEFAULT_SSID = "myc3_m3sh"
BACKHAUL_DEFAULT_PASSWORD = "myc3m3sh"


class BackhaulConfig(BaseModel):
    """Backhaul / AP mode configuration for USB WiFi adapter."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(False, description="Enable backhaul networking")
    interface: str = Field(
        "", description="USB WiFi interface (auto-detected if empty)"
    )
    mode: Literal["client", "ap", "disabled"] = Field(
        "disabled", description="Backhaul mode"
    )

    # Client mode
    client_ssid: str = Field(
        "", max_length=32, description="WiFi network SSID to connect to"
    )
    client_password: str = Field("", max_length=63, description="WiFi network password")

    # AP mode
    ap_ssid: str = Field(
        "myc3_m3sh", max_length=32, description="Access point SSID to broadcast"
    )
    ap_password: str = Field(
        "", max_length=63, description="AP password (min 8 chars if set)"
    )
    ap_channel: int = Field(
        1, ge=1, le=165, description="AP WiFi channel (ch1 avoids mesh on ch6)"
    )
    ap_band: Literal["2.4GHz", "5GHz"] = Field(
        "2.4GHz", description="AP WiFi band (2.4GHz avoids 5GHz uplink interference)"
    )
    ap_hidden: bool = Field(False, description="Hide AP SSID from broadcast")

    # NAT
    nat_enabled: bool = Field(True, description="Enable NAT for internet sharing")

    # Mesh bridge
    mesh_bridged: bool = Field(
        False,
        description="Bridge AP clients into BATMAN mesh (L2 access to all mesh nodes). "
        "When disabled (default), AP clients are isolated from the mesh but "
        "still receive internet access if NAT is enabled.",
    )

    @field_validator("interface")
    @classmethod
    def validate_interface(cls, v: str) -> str:
        if v and not re.match(r"^wlan[0-9]{1,2}$", v):
            raise ValueError(f"Invalid interface name: {v}. Must match wlanN format.")
        return v

    @field_validator("client_password", "ap_password")
    @classmethod
    def validate_password_chars(cls, v: str) -> str:
        if v and len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if v and re.search(r"[\x00-\x1f\x7f]", v):
            raise ValueError("Password must not contain control characters")
        if v and '"' in v:
            raise ValueError("Password must not contain double quotes")
        return v

    @field_validator("client_ssid", "ap_ssid")
    @classmethod
    def validate_backhaul_ssid(cls, v: str) -> str:
        if v and not re.match(r"^[A-Za-z0-9_ -]{1,32}$", v):
            raise ValueError(
                "SSID must be alphanumeric, spaces, hyphens, or underscores"
            )
        return v

    @model_validator(mode="after")
    def validate_ap_channel_for_band(self) -> BackhaulConfig:
        if self.mode == "ap" and self.enabled:
            if self.ap_band == "2.4GHz" and not (1 <= self.ap_channel <= 11):
                raise ValueError(
                    f"AP channel {self.ap_channel} invalid for 2.4GHz (must be 1-11)"
                )
            if (
                self.ap_band == "5GHz"
                and self.ap_channel not in MeshConfig._VALID_5GHZ_CHANNELS
            ):
                raise ValueError(
                    f"AP channel {self.ap_channel} is not a valid 5GHz channel"
                )
        return self

    @model_validator(mode="after")
    def validate_ap_has_password(self) -> BackhaulConfig:
        if self.mode == "ap" and self.enabled and not self.ap_password:
            raise ValueError("AP mode requires a password (WPA2, min 8 chars)")
        return self

    @model_validator(mode="after")
    def validate_client_has_credentials(self) -> BackhaulConfig:
        if self.mode == "client" and self.enabled:
            if not self.client_ssid:
                raise ValueError("Client mode requires an SSID")
            if not self.client_password:
                raise ValueError("Client mode requires a password")
        return self


class HaLowConfig(BaseModel):
    """HaLow radio settings (802.11ah via ESP32 HT-HC33)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(False, description="Enable HaLow as BATMAN transport")
    transport: Literal["usb-ecm", "serial"] = Field(
        "serial", description="Transport mode: usb-ecm (native USB Ethernet) or serial (SLIP bridge)"
    )
    serial_device: str = Field(
        "/dev/ttyUSB0", description="Serial device for SLIP bridge (serial mode only)"
    )
    interface: str = Field(
        "", description="HaLow network interface (auto-detect: usb0 or halow0)"
    )

    @field_validator("serial_device")
    @classmethod
    def validate_serial_device(cls, v: str) -> str:
        if v and not re.match(r"^/dev/tty(USB|ACM|S|AMA)\d{1,3}$", v):
            raise ValueError(f"Invalid serial device path: {v}")
        return v

    @field_validator("interface")
    @classmethod
    def validate_halow_interface(cls, v: str) -> str:
        if v and not re.match(r"^(halow0|usb[0-9])$", v):
            raise ValueError(f"Invalid HaLow interface: {v}. Must be halow0 or usbN.")
        return v


class DisplayConfig(BaseModel):
    """UI display settings."""

    model_config = ConfigDict(extra="forbid")

    crt_effects: bool = Field(True, description="Enable CRT shader effects")
    scanlines: bool = Field(True, description="Enable scanline overlay")
    phosphor_glow: bool = Field(True, description="Enable phosphor glow effect")
    brightness: int = Field(100, ge=10, le=100, description="Display brightness %")
    color_scheme: Literal["classic", "amber", "green"] = Field(
        "classic", description="Color scheme"
    )


class SystemConfig(BaseModel):
    """System-level settings."""

    model_config = ConfigDict(extra="forbid")

    hostname: str = Field(
        "myc3",
        max_length=63,
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$",
        description="System hostname (accessible as <hostname>.local)",
    )
    timezone: str = Field("UTC", max_length=64, description="System timezone")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Logging level"
    )
    auto_start_meshtastic: bool = Field(
        True, description="Start Meshtastic service on boot"
    )
    api_key: str = Field(
        "", max_length=128, description="API key for protected endpoints (legacy)"
    )
    setup_complete: bool = Field(
        False, description="Set to true after first-boot setup wizard completes"
    )
    require_auth: bool = Field(
        False, description="Require user authentication (JWT) for all endpoints"
    )
    jwt_secret: str = Field(
        "", max_length=128, description="JWT signing secret (auto-generated if empty)"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z_]+(/[A-Za-z_]+)*$", v):
            raise ValueError(f"Invalid timezone format: {v}")
        return v


class Myc3liumConfig(BaseModel):
    """Top-level configuration combining all sections."""

    radio: RadioConfig = Field(default_factory=lambda: RadioConfig())
    mesh: MeshConfig = Field(default_factory=lambda: MeshConfig())
    backhaul: BackhaulConfig = Field(default_factory=lambda: BackhaulConfig())
    halow: HaLowConfig = Field(default_factory=lambda: HaLowConfig())
    display: DisplayConfig = Field(default_factory=lambda: DisplayConfig())
    system: SystemConfig = Field(default_factory=lambda: SystemConfig())


class Myc3liumConfigPublic(BaseModel):
    """Config response model that masks sensitive fields."""

    radio: RadioConfig
    mesh: MeshConfig
    backhaul: dict
    halow: HaLowConfig
    display: DisplayConfig
    system: dict

    @staticmethod
    def from_config(config: Myc3liumConfig) -> Myc3liumConfigPublic:
        system_data = config.system.model_dump()
        system_data["api_key"] = "***" if system_data.get("api_key") else ""
        system_data["jwt_secret"] = "***" if system_data.get("jwt_secret") else ""

        backhaul_data = config.backhaul.model_dump()
        backhaul_data["client_password"] = (
            "***" if backhaul_data.get("client_password") else ""
        )
        backhaul_data["ap_password"] = "***" if backhaul_data.get("ap_password") else ""

        return Myc3liumConfigPublic(
            radio=config.radio,
            mesh=config.mesh,
            backhaul=backhaul_data,
            halow=config.halow,
            display=config.display,
            system=system_data,
        )
