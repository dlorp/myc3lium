"""Helper functions for WebSocket testing"""

import time
from typing import Optional


def receive_json_with_timeout(websocket, timeout: float = 2.0) -> Optional[dict]:
    """
    Receive JSON from WebSocket with timeout

    Args:
        websocket: WebSocket test session
        timeout: Timeout in seconds

    Returns:
        Received JSON data or None if timeout

    Raises:
        Exception: If timeout occurs
    """
    # Note: The current TestClient doesn't support timeout on receive_json
    # This is a simplified implementation that just receives immediately
    # In production tests, you'd use asyncio timeout or similar
    try:
        return websocket.receive_json()
    except Exception as e:
        raise TimeoutError(f"WebSocket receive timed out after {timeout}s") from e


def wait_for_websocket_event(
    websocket, event_type: str, timeout: float = 2.0, skip_initial: int = 0
) -> dict:
    """
    Wait for a specific WebSocket event type

    Args:
        websocket: WebSocket test session
        event_type: Event type to wait for
        timeout: Timeout in seconds
        skip_initial: Number of initial messages to skip (e.g., welcome, stats)

    Returns:
        The matching event

    Raises:
        TimeoutError: If event not received within timeout
    """
    start_time = time.time()

    # Skip initial messages
    for _ in range(skip_initial):
        try:
            websocket.receive_json()
        except Exception:
            pass

    # Wait for the target event
    while time.time() - start_time < timeout:
        try:
            event = websocket.receive_json()
            if event.get("event") == event_type:
                return event
        except Exception:
            # If no message available, continue waiting
            time.sleep(0.01)

    raise TimeoutError(f"Event '{event_type}' not received within {timeout}s")
