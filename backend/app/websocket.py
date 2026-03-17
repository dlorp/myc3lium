from typing import Optional
"""WebSocket connection manager for real-time updates"""

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    MAX_CONNECTIONS = 100

    def __init__(self):
        # Active connections indexed by client ID
        self.active_connections: dict[str, WebSocket] = {}
        # Connection counter for generating client IDs
        self._client_counter = 0

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection and return client ID"""
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1008, reason="Server at capacity")
            raise ValueError("Max connections reached")

        await websocket.accept()
        client_id = f"client_{self._client_counter}"
        self._client_counter += 1
        self.active_connections[client_id] = websocket
        return client_id

    def disconnect(self, client_id: str):
        """Remove a disconnected client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception:
                # Client disconnected, remove from pool
                self.disconnect(client_id)

    async def broadcast(self, message: dict, exclude: Optional[set[str]] = None):
        """Broadcast message to all connected clients (optionally excluding some)"""
        exclude = exclude or set()
        disconnected = []

        for client_id, websocket in self.active_connections.items():
            if client_id in exclude:
                continue

            try:
                await websocket.send_json(message)
            except Exception:
                # Mark for removal
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
