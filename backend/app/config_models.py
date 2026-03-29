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
        "", max_length=128, description="API key for protected endpoints"
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
    display: DisplayConfig = Field(default_factory=lambda: DisplayConfig())
    system: SystemConfig = Field(default_factory=lambda: SystemConfig())


class Myc3liumConfigPublic(BaseModel):
    """Config response model that masks the API key."""

    radio: RadioConfig
    mesh: MeshConfig
    display: DisplayConfig
    system: dict

    @staticmethod
    def from_config(config: Myc3liumConfig) -> Myc3liumConfigPublic:
        system_data = config.system.model_dump()
        system_data["api_key"] = "***" if system_data.get("api_key") else ""
        return Myc3liumConfigPublic(
            radio=config.radio,
            mesh=config.mesh,
            display=config.display,
            system=system_data,
        )
