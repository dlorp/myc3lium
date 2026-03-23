"""Application configuration"""

import platform

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    app_name: str = "MYC3LIUM"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Auto-detect: use live data on Linux (Pi), mock on Mac
    use_live_data: bool = platform.system() == "Linux"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MYC3LIUM_")


settings = Settings()
