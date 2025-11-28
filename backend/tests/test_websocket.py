"""Tests for WebSocket real-time updates."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from backend.realtime.websocket_manager import (
    WebSocketManager,
    ConnectedClient,
    Subscription,
    MessageType,
)


@pytest.fixture
def ws_manager():
    """Create a fresh WebSocket manager for each test."""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestSubscription:
    """Tests for Subscription class."""

    def test_default_subscription(self):
        """Default subscription should have all_events=True."""
        sub = Subscription()

        assert sub.all_events is True
        assert len(sub.regions) == 0
        assert len(sub.categories) == 0

    def test_subscription_with_filters(self):
        """Subscription with specific filters."""
        sub = Subscription(
            regions={"europe", "africa"},
            categories={"conflict"},
            all_events=False,
        )

        assert "europe" in sub.regions
        assert "conflict" in sub.categories
        assert sub.all_events is False


class TestConnectedClient:
    """Tests for ConnectedClient class."""

    def test_create_client(self, mock_websocket):
        """Test creating a connected client."""
        client = ConnectedClient(
            websocket=mock_websocket,
            client_id="test-123",
            connected_at=datetime.utcnow(),
        )

        assert client.client_id == "test-123"
        assert client.websocket == mock_websocket
        assert isinstance(client.subscription, Subscription)


class TestWebSocketManager:
    """Tests for WebSocketManager."""

    def test_initial_state(self, ws_manager):
        """Test initial manager state."""
        assert ws_manager.client_count == 0

    @pytest.mark.asyncio
    async def test_connect_client(self, ws_manager, mock_websocket):
        """Test client connection."""
        client = await ws_manager.connect(mock_websocket, "client-1")

        assert client is not None
        assert client.client_id == "client-1"
        assert ws_manager.client_count == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_client(self, ws_manager, mock_websocket):
        """Test client disconnection."""
        await ws_manager.connect(mock_websocket, "client-1")
        await ws_manager.disconnect("client-1")

        assert ws_manager.client_count == 0

    @pytest.mark.asyncio
    async def test_update_subscription(self, ws_manager, mock_websocket):
        """Test updating client subscription."""
        await ws_manager.connect(mock_websocket, "client-1")

        await ws_manager.update_subscription("client-1", {
            "regions": ["europe", "africa"],
            "categories": ["conflict"],
            "all_events": False,
        })

        # Access the client's subscription
        client = ws_manager._clients["client-1"]
        assert "europe" in client.subscription.regions
        assert "africa" in client.subscription.regions
        assert "conflict" in client.subscription.categories
        assert client.subscription.all_events is False

    @pytest.mark.asyncio
    async def test_broadcast_event_to_all(self, ws_manager, mock_websocket):
        """Test broadcasting an event to all clients."""
        await ws_manager.connect(mock_websocket, "client-1")

        event = {
            "id": "test-1",
            "title": "Test Event",
            "region": "Europe",
            "threat_level": "high",
        }

        sent_count = await ws_manager.broadcast_event(event)

        assert sent_count == 1
        # Check that send_json was called (once for connect ack, once for event)
        assert mock_websocket.send_json.call_count >= 1

    @pytest.mark.asyncio
    async def test_broadcast_respects_subscription(self, ws_manager):
        """Test that broadcast respects subscription filters."""
        # Create two mock websockets
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await ws_manager.connect(ws1, "client-1")
        await ws_manager.connect(ws2, "client-2")

        # Set different subscriptions
        await ws_manager.update_subscription("client-1", {
            "regions": ["europe"],
            "all_events": False,
        })
        await ws_manager.update_subscription("client-2", {
            "regions": ["asia"],
            "all_events": False,
        })

        # Reset call counts after connection ack
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        # Broadcast Europe event
        await ws_manager.broadcast_event({"region": "europe", "threat_level": "high"})

        # Only client1 should receive it
        ws1.send_json.assert_called()
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_alert(self, ws_manager, mock_websocket):
        """Test broadcasting an alert."""
        await ws_manager.connect(mock_websocket, "client-1")
        mock_websocket.send_json.reset_mock()

        alert = {
            "id": "alert-1",
            "title": "Critical Alert",
            "priority": "critical",
        }

        sent_count = await ws_manager.broadcast_alert(alert)

        assert sent_count == 1
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.ALERT_TRIGGERED

    @pytest.mark.asyncio
    async def test_broadcast_report(self, ws_manager, mock_websocket):
        """Test broadcasting a report notification."""
        await ws_manager.connect(mock_websocket, "client-1")
        mock_websocket.send_json.reset_mock()

        report = {
            "id": "report-1",
            "title": "Daily Summary",
        }

        sent_count = await ws_manager.broadcast_report(report)

        assert sent_count == 1
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == MessageType.REPORT_GENERATED


class TestMessageHandling:
    """Tests for client message handling."""

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, ws_manager, mock_websocket):
        """Test handling ping message from client."""
        await ws_manager.connect(mock_websocket, "client-1")
        mock_websocket.send_json.reset_mock()

        message = {"type": MessageType.PING}
        await ws_manager.handle_client_message("client-1", message)

        # Should respond with pong
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self, ws_manager, mock_websocket):
        """Test handling subscribe message from client."""
        await ws_manager.connect(mock_websocket, "client-1")

        message = {
            "type": MessageType.SUBSCRIBE,
            "data": {
                "regions": ["europe"],
                "categories": ["conflict"],
            }
        }

        await ws_manager.handle_client_message("client-1", message)

        client = ws_manager._clients["client-1"]
        assert "europe" in client.subscription.regions

    @pytest.mark.asyncio
    async def test_handle_unsubscribe_message(self, ws_manager, mock_websocket):
        """Test handling unsubscribe message from client."""
        await ws_manager.connect(mock_websocket, "client-1")

        # First subscribe
        await ws_manager.update_subscription("client-1", {
            "regions": ["europe"],
            "all_events": False,
        })

        # Then unsubscribe
        message = {"type": MessageType.UNSUBSCRIBE}
        await ws_manager.handle_client_message("client-1", message)

        # Should reset to default subscription
        client = ws_manager._clients["client-1"]
        assert client.subscription.all_events is True
        assert len(client.subscription.regions) == 0


class TestSubscriptionFiltering:
    """Tests for subscription-based event filtering."""

    @pytest.fixture
    def manager_with_client(self, ws_manager, mock_websocket):
        """Create a manager with a connected client."""
        async def setup():
            await ws_manager.connect(mock_websocket, "client-1")
            return ws_manager
        return setup

    def test_should_receive_all_events(self, ws_manager, mock_websocket):
        """Test that default subscription receives all events."""
        client = ConnectedClient(
            websocket=mock_websocket,
            client_id="test",
            connected_at=datetime.utcnow(),
        )

        event = {"region": "anywhere", "category": "anything", "threat_level": "any"}
        assert ws_manager._should_receive(client, event) is True

    def test_should_receive_matching_region(self, ws_manager, mock_websocket):
        """Test region-based filtering."""
        client = ConnectedClient(
            websocket=mock_websocket,
            client_id="test",
            connected_at=datetime.utcnow(),
            subscription=Subscription(regions={"europe"}, all_events=False),
        )

        # Matching region
        assert ws_manager._should_receive(client, {"region": "europe"}) is True
        assert ws_manager._should_receive(client, {"region": "Europe"}) is True

        # Non-matching region
        assert ws_manager._should_receive(client, {"region": "asia"}) is False

    def test_should_receive_matching_category(self, ws_manager, mock_websocket):
        """Test category-based filtering."""
        client = ConnectedClient(
            websocket=mock_websocket,
            client_id="test",
            connected_at=datetime.utcnow(),
            subscription=Subscription(categories={"conflict"}, all_events=False),
        )

        # Matching category
        assert ws_manager._should_receive(client, {"category": "conflict"}) is True

        # Non-matching category
        assert ws_manager._should_receive(client, {"category": "disaster"}) is False
