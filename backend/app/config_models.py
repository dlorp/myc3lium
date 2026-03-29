"""
User-facing configuration models for MYC3LIUM.

These define the TOML config file structure at /opt/myc3lium/config/myc3lium.toml.
Separate from app/config.py which handles internal app settings via env vars.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RadioConfig(BaseModel):
    """Radio hardware settings."""

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


class MeshConfig(BaseModel):
    """Mesh networking settings."""

    batman_channel: int = Field(
        6, ge=1, le=11, description="WiFi channel for BATMAN mesh"
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


class DisplayConfig(BaseModel):
    """UI display settings."""

    crt_effects: bool = Field(True, description="Enable CRT shader effects")
    scanlines: bool = Field(True, description="Enable scanline overlay")
    phosphor_glow: bool = Field(True, description="Enable phosphor glow effect")
    brightness: int = Field(100, ge=10, le=100, description="Display brightness %")
    color_scheme: str = Field(
        "classic", description="Color scheme (classic, amber, green)"
    )


class SystemConfig(BaseModel):
    """System-level settings."""

    hostname: str = Field(
        "myc3",
        max_length=63,
        description="System hostname (accessible as <hostname>.local)",
    )
    timezone: str = Field("UTC", max_length=64, description="System timezone")
    log_level: str = Field(
        "INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    auto_start_meshtastic: bool = Field(
        True, description="Start Meshtastic service on boot"
    )
    api_key: str = Field(
        "", max_length=128, description="API key for protected endpoints"
    )


class Myc3liumConfig(BaseModel):
    """Top-level configuration combining all sections."""

    radio: RadioConfig = Field(default_factory=RadioConfig)
    mesh: MeshConfig = Field(default_factory=MeshConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
