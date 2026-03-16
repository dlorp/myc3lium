"""Application configuration"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    app_name: str = "MYC3LIUM"
    debug: bool = False
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = ConfigDict(env_file=".env")


settings = Settings()
