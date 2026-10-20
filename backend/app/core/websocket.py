"""
WebSocket Connection Manager for Real-Time Dashboard Broadcasting.
Pushes live telemetry events, discrepancy alerts, and pipeline progress to connected clients.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket] Client connected. Total active connections: {len(self.active_connections)}")
        # Send welcome event
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Pramaan AI Live Telemetry Stream",
            "timestamp": datetime.utcnow().isoformat()
        }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"[WebSocket] Client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcasts a JSON payload to all connected WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[WebSocket] Failed to send message to client: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


# Global singleton instance
ws_manager = ConnectionManager()
