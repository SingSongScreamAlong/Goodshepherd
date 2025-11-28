"""WebSocket connection manager for real-time event broadcasting."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WebSocket messages."""

    # Server -> Client
    EVENT_NEW = "event:new"
    EVENT_UPDATE = "event:update"
    ALERT_TRIGGERED = "alert:triggered"
    REPORT_GENERATED = "report:generated"
    CONNECTION_ACK = "connection:ack"
    HEARTBEAT = "heartbeat"
    ERROR = "error"

    # Client -> Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"


@dataclass
class Subscription:
    """Client subscription preferences."""

    regions: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    threat_levels: Set[str] = field(default_factory=set)
    all_events: bool = True  # Subscribe to all by default


@dataclass
class ConnectedClient:
    """Represents a connected WebSocket client."""

    websocket: WebSocket
    client_id: str
    connected_at: datetime
    subscription: Subscription = field(default_factory=Subscription)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self._clients: dict[str, ConnectedClient] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_interval = 30  # seconds
        self._heartbeat_task: asyncio.Task | None = None

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self._clients)

    async def start(self) -> None:
        """Start the WebSocket manager background tasks."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop the WebSocket manager."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        logger.info("WebSocket manager stopped")

    async def connect(self, websocket: WebSocket, client_id: str) -> ConnectedClient:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        client = ConnectedClient(
            websocket=websocket,
            client_id=client_id,
            connected_at=datetime.utcnow(),
        )

        async with self._lock:
            self._clients[client_id] = client

        # Send connection acknowledgment
        await self._send_to_client(client, {
            "type": MessageType.CONNECTION_ACK,
            "client_id": client_id,
            "connected_at": client.connected_at.isoformat(),
            "server_time": datetime.utcnow().isoformat(),
        })

        logger.info(f"Client {client_id} connected. Total clients: {self.client_count}")
        return client

    async def disconnect(self, client_id: str) -> None:
        """Remove a disconnected client."""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(f"Client {client_id} disconnected. Total clients: {self.client_count}")

    async def update_subscription(self, client_id: str, subscription_data: dict) -> None:
        """Update a client's subscription preferences."""
        async with self._lock:
            if client_id not in self._clients:
                return

            client = self._clients[client_id]
            sub = client.subscription

            if "regions" in subscription_data:
                sub.regions = set(subscription_data["regions"])
            if "categories" in subscription_data:
                sub.categories = set(subscription_data["categories"])
            if "threat_levels" in subscription_data:
                sub.threat_levels = set(subscription_data["threat_levels"])
            if "all_events" in subscription_data:
                sub.all_events = subscription_data["all_events"]

        logger.debug(f"Updated subscription for client {client_id}")

    async def broadcast_event(self, event_data: dict, message_type: MessageType = MessageType.EVENT_NEW) -> int:
        """Broadcast an event to all subscribed clients."""
        message = {
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data,
        }

        sent_count = 0
        async with self._lock:
            clients = list(self._clients.values())

        for client in clients:
            if self._should_receive(client, event_data):
                try:
                    await self._send_to_client(client, message)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send to client {client.client_id}: {e}")

        return sent_count

    async def broadcast_alert(self, alert_data: dict) -> int:
        """Broadcast an alert to all connected clients."""
        message = {
            "type": MessageType.ALERT_TRIGGERED,
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data,
        }

        sent_count = 0
        async with self._lock:
            clients = list(self._clients.values())

        for client in clients:
            try:
                await self._send_to_client(client, message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send alert to client {client.client_id}: {e}")

        return sent_count

    async def broadcast_report(self, report_data: dict) -> int:
        """Broadcast a new report notification."""
        message = {
            "type": MessageType.REPORT_GENERATED,
            "timestamp": datetime.utcnow().isoformat(),
            "data": report_data,
        }

        sent_count = 0
        async with self._lock:
            clients = list(self._clients.values())

        for client in clients:
            try:
                await self._send_to_client(client, message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send report to client {client.client_id}: {e}")

        return sent_count

    async def handle_client_message(self, client_id: str, message: dict) -> None:
        """Handle incoming message from a client."""
        msg_type = message.get("type")

        if msg_type == MessageType.PING:
            async with self._lock:
                if client_id in self._clients:
                    self._clients[client_id].last_heartbeat = datetime.utcnow()
            # Respond with pong
            await self._send_to_client_by_id(client_id, {"type": "pong"})

        elif msg_type == MessageType.SUBSCRIBE:
            await self.update_subscription(client_id, message.get("data", {}))

        elif msg_type == MessageType.UNSUBSCRIBE:
            # Reset to default subscription
            async with self._lock:
                if client_id in self._clients:
                    self._clients[client_id].subscription = Subscription()

    def _should_receive(self, client: ConnectedClient, event_data: dict) -> bool:
        """Check if a client should receive an event based on subscription."""
        sub = client.subscription

        # If subscribed to all, always receive
        if sub.all_events:
            return True

        # Check region filter
        if sub.regions:
            event_region = (event_data.get("region") or "").lower()
            if event_region and event_region not in {r.lower() for r in sub.regions}:
                return False

        # Check category filter
        if sub.categories:
            event_category = (event_data.get("category") or "").lower()
            if event_category and event_category not in {c.lower() for c in sub.categories}:
                return False

        # Check threat level filter
        if sub.threat_levels:
            event_threat = (event_data.get("threat_level") or "").lower()
            if event_threat and event_threat not in {t.lower() for t in sub.threat_levels}:
                return False

        return True

    async def _send_to_client(self, client: ConnectedClient, message: dict) -> None:
        """Send a message to a specific client."""
        await client.websocket.send_json(message)

    async def _send_to_client_by_id(self, client_id: str, message: dict) -> None:
        """Send a message to a client by ID."""
        async with self._lock:
            if client_id in self._clients:
                await self._clients[client_id].websocket.send_json(message)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to all clients."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                message = {
                    "type": MessageType.HEARTBEAT,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                async with self._lock:
                    clients = list(self._clients.values())

                for client in clients:
                    try:
                        await self._send_to_client(client, message)
                    except Exception:
                        # Client will be cleaned up on next interaction
                        pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def get_ws_manager() -> WebSocketManager:
    """Dependency to get the WebSocket manager."""
    return ws_manager
