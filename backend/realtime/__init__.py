"""Real-time communication module for Good Shepherd."""

from .websocket_manager import (
    MessageType,
    WebSocketManager,
    ws_manager,
    get_ws_manager,
)

__all__ = [
    "MessageType",
    "WebSocketManager",
    "ws_manager",
    "get_ws_manager",
]
