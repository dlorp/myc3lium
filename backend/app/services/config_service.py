"""
TOML-based configuration service for MYC3LIUM.

Reads and writes user configuration from /opt/myc3lium/config/myc3lium.toml (production)
or ./myc3lium.toml (development). Falls back to defaults if no config file exists.
"""

from __future__ import annotations

import logging
import platform
import tomllib
from pathlib import Path

import tomli_w

from app.config_models import Myc3liumConfig

logger = logging.getLogger(__name__)

# Config file paths
_PROD_CONFIG_PATH = Path("/opt/myc3lium/config/myc3lium.toml")
_DEV_CONFIG_PATH = Path("./myc3lium.toml")

# Valid config section names
VALID_SECTIONS = {"radio", "mesh", "display", "system"}

# Services that can be restarted via API (whitelist)
RESTARTABLE_SERVICES = {
    "reticulum",
    "myc3lium-backend",
    "lora-bridge",
}


class ConfigService:
    """Manages reading and writing TOML configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        if config_path:
            self._config_path = config_path
        elif platform.system() == "Linux":
            self._config_path = _PROD_CONFIG_PATH
        else:
            self._config_path = _DEV_CONFIG_PATH

        self._config: Myc3liumConfig = self._load()

    def _load(self) -> Myc3liumConfig:
        """Load config from TOML file, falling back to defaults."""
        if not self._config_path.exists():
            logger.info(
                "No config file at %s — using defaults (first boot)",
                self._config_path,
            )
            return Myc3liumConfig()

        try:
            with open(self._config_path, "rb") as f:
                raw = tomllib.load(f)
            config = Myc3liumConfig.model_validate(raw)
            logger.info("Loaded config from %s", self._config_path)
            return config
        except Exception as e:
            logger.error(
                "Failed to load config from %s: %s — using defaults",
                self._config_path,
                e,
            )
            return Myc3liumConfig()

    @property
    def config(self) -> Myc3liumConfig:
        """Get the current configuration."""
        return self._config

    @property
    def config_path(self) -> Path:
        """Get the config file path."""
        return self._config_path

    def is_first_boot(self) -> bool:
        """Check if this is the first boot (no config file exists)."""
        return not self._config_path.exists()

    def get_section(self, section: str) -> dict:
        """
        Get a single config section as a dict.

        Args:
            section: Section name (radio, mesh, display, system)

        Returns:
            Section data as dict

        Raises:
            ValueError: If section name is invalid
        """
        if section not in VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}. Valid: {VALID_SECTIONS}")
        return getattr(self._config, section).model_dump()

    def update_section(self, section: str, updates: dict) -> dict:
        """
        Partially update a config section and persist to disk.

        Args:
            section: Section name (radio, mesh, display, system)
            updates: Partial dict of fields to update

        Returns:
            Updated section data as dict

        Raises:
            ValueError: If section name is invalid or validation fails
        """
        if section not in VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}. Valid: {VALID_SECTIONS}")

        # Get current section, merge updates, validate
        current = getattr(self._config, section).model_dump()
        current.update(updates)

        # Reconstruct the section model (validates the merged data)
        section_model_cls = type(getattr(self._config, section))
        updated_section = section_model_cls.model_validate(current)

        # Apply to in-memory config
        setattr(self._config, section, updated_section)

        # Persist to disk
        self._save()

        logger.info("Updated config section [%s]: %s", section, list(updates.keys()))
        return updated_section.model_dump()

    def create_default_config(self) -> None:
        """Write default configuration to disk (for first boot)."""
        self._config = Myc3liumConfig()
        self._save()
        logger.info("Created default config at %s", self._config_path)

    def _save(self) -> None:
        """Persist current config to TOML file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._config.model_dump()
        with open(self._config_path, "wb") as f:
            tomli_w.dump(data, f)

        logger.debug("Saved config to %s", self._config_path)

    def reload(self) -> Myc3liumConfig:
        """Reload config from disk."""
        self._config = self._load()
        return self._config

    @staticmethod
    def restart_service(service_name: str) -> tuple[bool, str]:
        """
        Restart a systemd service (Linux only, whitelisted services).

        Args:
            service_name: Name of the service to restart

        Returns:
            Tuple of (success, message)
        """
        if service_name not in RESTARTABLE_SERVICES:
            return False, f"Service '{service_name}' is not in the allowed list"

        if platform.system() != "Linux":
            return False, "Service restart only available on Linux (Pi)"

        import subprocess

        try:
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("Restarted service: %s", service_name)
                return True, f"Service '{service_name}' restarted successfully"
            else:
                logger.error(
                    "Failed to restart %s: %s", service_name, result.stderr.strip()
                )
                return False, f"Service '{service_name}' failed to restart"
        except subprocess.TimeoutExpired:
            return False, f"Service restart timed out for '{service_name}'"
        except Exception as e:
            logger.error("Error restarting service %s: %s", service_name, e)
            return False, "Service restart failed"
