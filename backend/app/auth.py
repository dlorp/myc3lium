"""Simple API key authentication for Meshtastic endpoints"""

import hmac
import logging
import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

API_KEY = os.getenv("MESHTASTIC_API_KEY")
if not API_KEY:
    logger.warning(
        "MESHTASTIC_API_KEY not set — send endpoint is unprotected. "
        "Set this environment variable in production."
    )

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints"""
    if not API_KEY:
        # No key configured — skip auth (dev mode)
        return api_key
    if not hmac.compare_digest(api_key or "", API_KEY):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key
