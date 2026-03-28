"""Simple API key authentication for Meshtastic endpoints"""

import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("MESHTASTIC_API_KEY", "dev-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints"""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key
