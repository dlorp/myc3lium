"""
MYC3LIUM Security Module
Authentication, validation, privacy controls
"""

import hashlib
import hmac
import re
import secrets
import time
from functools import wraps
from typing import Any, Optional

from fastapi import Header, HTTPException, WebSocket


class SecurityManager:
    """
    Centralized security management
    - ATAK CoT message signing
    - WebSocket authentication
    - Input validation
    - Privacy controls
    """

    def __init__(self, shared_key: Optional[str] = None):
        # Load from environment or generate
        self.shared_key = shared_key or secrets.token_hex(32)
        self.api_tokens = set()

        # Privacy settings
        self.privacy_mode = False
        self.position_quantization = 50.0  # meters
        self.update_jitter_range = (1.0, 10.0)  # seconds
        self.geofence_blacklist = []  # List of (lat, lon, radius) tuples

        # Rate limiting
        self.rate_limits = {}

    def sign_cot_message(self, cot_xml: str) -> str:
        """
        Sign ATAK CoT message with HMAC-SHA256
        Appends signature to <detail> block

        Args:
            cot_xml: Original CoT XML

        Returns:
            Signed CoT XML with <auth> element
        """
        # Generate signature
        signature = hmac.new(
            self.shared_key.encode(), cot_xml.encode(), hashlib.sha256
        ).hexdigest()

        # Inject signature before closing </detail>
        if "</detail>" in cot_xml:
            auth_block = f'    <auth method="HMAC-SHA256" sig="{signature}"/>\n'
            signed_xml = cot_xml.replace("</detail>", auth_block + "</detail>")
            return signed_xml
        else:
            raise ValueError("Invalid CoT XML: missing </detail>")

    def verify_cot_message(self, cot_xml: str) -> bool:
        """
        Verify ATAK CoT message signature

        Returns:
            True if signature valid, False otherwise
        """
        # Extract signature
        import re

        sig_match = re.search(
            r'<auth method="HMAC-SHA256" sig="([0-9a-f]+)"/>', cot_xml
        )

        if not sig_match:
            return False  # No signature found

        received_sig = sig_match.group(1)

        # Remove signature for verification
        unsigned_xml = re.sub(
            r'    <auth method="HMAC-SHA256" sig="[0-9a-f]+"/>\n', "", cot_xml
        )

        # Compute expected signature
        expected_sig = hmac.new(
            self.shared_key.encode(), unsigned_xml.encode(), hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(received_sig, expected_sig)

    def generate_api_token(self) -> str:
        """
        Generate new API token for WebSocket authentication
        """
        token = secrets.token_urlsafe(32)
        self.api_tokens.add(token)
        return token

    def verify_api_token(self, token: str) -> bool:
        """
        Verify API token
        """
        return token in self.api_tokens

    def revoke_api_token(self, token: str):
        """
        Revoke API token
        """
        self.api_tokens.discard(token)

    async def authenticate_websocket(self, websocket: WebSocket) -> bool:
        """
        Authenticate WebSocket connection
        Checks for Authorization header or query parameter

        Returns:
            True if authenticated, False otherwise
        """
        # Check Authorization header
        token = websocket.headers.get("Authorization")

        # Fallback to query parameter (less secure but convenient)
        if not token:
            token = websocket.query_params.get("token")

        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return False

        # Strip "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]

        if not self.verify_api_token(token):
            await websocket.close(code=1008, reason="Invalid authentication token")
            return False

        return True

    def validate_observation_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and sanitize observation metadata

        Raises:
            ValueError: If metadata invalid

        Returns:
            Sanitized metadata
        """
        import json

        # Size limit: 1KB
        metadata_json = json.dumps(metadata)
        if len(metadata_json) > 1024:
            raise ValueError(
                f"Metadata too large: {len(metadata_json)} bytes (max 1KB)"
            )

        # Schema validation (basic)
        allowed_keys = {
            "value",
            "intensity",
            "description",
            "category",
            "confidence",
            "timestamp",
        }

        sanitized = {}
        for key, value in metadata.items():
            if key not in allowed_keys:
                continue  # Drop unknown keys

            # Sanitize strings (prevent XSS)
            if isinstance(value, str):
                value = value[:256]  # Max 256 chars per string
                value = re.sub(r'[<>&"]', "", value)  # Strip HTML chars

            sanitized[key] = value

        return sanitized

    def apply_privacy_filter(self, lat: float, lon: float) -> tuple[float, float]:
        """
        Apply privacy controls to position

        Returns:
            (filtered_lat, filtered_lon)
        """
        if not self.privacy_mode:
            return (lat, lon)

        # Check geofence blacklist
        for fence_lat, fence_lon, radius_m in self.geofence_blacklist:
            distance = self._haversine_distance(lat, lon, fence_lat, fence_lon)
            if distance < radius_m:
                # Inside blacklist zone - return quantized position outside zone
                lat, lon = self._push_outside_geofence(
                    lat, lon, fence_lat, fence_lon, radius_m
                )

        # Quantize to grid (±50m)
        if self.position_quantization > 0:
            # Convert to meters
            lat_m = lat * 111320
            lon_m = lon * 111320

            # Snap to grid
            lat_m = (
                round(lat_m / self.position_quantization) * self.position_quantization
            )
            lon_m = (
                round(lon_m / self.position_quantization) * self.position_quantization
            )

            # Convert back
            lat = lat_m / 111320
            lon = lon_m / 111320

        return (lat, lon)

    def get_update_jitter(self) -> float:
        """
        Get randomized update interval for privacy

        Returns:
            Seconds to wait before next update
        """
        if not self.privacy_mode:
            return 1.0  # Default 1 second

        import random

        return random.uniform(*self.update_jitter_range)

    def rate_limit(
        self, client_id: str, endpoint: str, max_per_minute: int = 60
    ) -> bool:
        """
        Rate limiting check

        Returns:
            True if allowed, False if rate limited
        """
        key = f"{client_id}:{endpoint}"
        now = time.time()

        if key not in self.rate_limits:
            self.rate_limits[key] = []

        # Clean old entries (>60s)
        self.rate_limits[key] = [t for t in self.rate_limits[key] if now - t < 60]

        if len(self.rate_limits[key]) >= max_per_minute:
            return False  # Rate limited

        self.rate_limits[key].append(now)
        return True

    def validate_interface_name(self, interface: str) -> bool:
        """
        Validate network interface name (prevent command injection)

        Returns:
            True if valid, False otherwise
        """
        # Allowlist: wlan0-9, eth0-9, lo, bat0
        pattern = r"^(wlan[0-9]|eth[0-9]|lo|bat0)$"
        return re.match(pattern, interface) is not None

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points in meters
        """
        import math

        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _push_outside_geofence(
        self,
        lat: float,
        lon: float,
        fence_lat: float,
        fence_lon: float,
        radius_m: float,
    ) -> tuple[float, float]:
        """
        Move position outside geofence zone
        """
        import math

        # Calculate bearing from fence center to position
        delta_lon = lon - fence_lon
        y = math.sin(math.radians(delta_lon)) * math.cos(math.radians(lat))
        x = math.cos(math.radians(fence_lat)) * math.sin(math.radians(lat)) - math.sin(
            math.radians(fence_lat)
        ) * math.cos(math.radians(lat)) * math.cos(math.radians(delta_lon))
        bearing = math.atan2(y, x)

        # Move position to fence edge + buffer (10m)
        distance_m = radius_m + 10

        # Convert to lat/lon offset
        R = 6371000
        lat_offset = (distance_m / R) * (180 / math.pi)
        lon_offset = (
            (distance_m / R) * (180 / math.pi) / math.cos(math.radians(fence_lat))
        )

        new_lat = fence_lat + lat_offset * math.cos(bearing)
        new_lon = fence_lon + lon_offset * math.sin(bearing)

        return (new_lat, new_lon)


# Decorator for WebSocket authentication
def require_auth(security_manager: SecurityManager):
    """
    Decorator to require authentication on WebSocket endpoints
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(websocket: WebSocket, *args, **kwargs):
            if not await security_manager.authenticate_websocket(websocket):
                return  # Connection closed by authenticate_websocket

            return await func(websocket, *args, **kwargs)

        return wrapper

    return decorator


# Decorator for REST API token validation
def require_api_token(security_manager: SecurityManager):
    """
    Decorator to require API token on REST endpoints
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, authorization: Optional[str] = Header(None), **kwargs):
            if not authorization:
                raise HTTPException(
                    status_code=401, detail="Missing authorization header"
                )

            token = authorization
            if token.startswith("Bearer "):
                token = token[7:]

            if not security_manager.verify_api_token(token):
                raise HTTPException(status_code=401, detail="Invalid token")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Test security manager
    security = SecurityManager()

    # Test CoT signing
    cot_xml = """<?xml version="1.0"?>
<event version="2.0" uid="test_node" type="a-f-G-E-S">
  <point lat="47.606" lon="-122.332" hae="125"/>
  <detail>
    <contact callsign="TEST"/>
  </detail>
</event>"""

    signed = security.sign_cot_message(cot_xml)
    print("Signed CoT:")
    print(signed)

    # Verify
    is_valid = security.verify_cot_message(signed)
    print(f"\nSignature valid: {is_valid}")

    # Test privacy filter
    security.privacy_mode = True
    security.position_quantization = 50.0

    lat, lon = security.apply_privacy_filter(47.60621, -122.33207)
    print("\nOriginal: 47.60621, -122.33207")
    print(f"Filtered: {lat:.5f}, {lon:.5f}")
