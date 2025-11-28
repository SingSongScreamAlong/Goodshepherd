"""Alert engine background worker.

Continuously processes events and triggers notifications.
Run with: python -m backend.workers.alert_worker
"""

import asyncio
import logging
import os
import signal
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.alerts.alert_engine import AlertEngine, AlertEngineConfig
from backend.database.session import async_session_factory

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AlertWorker:
    """Background worker for the alert engine."""

    def __init__(self):
        self.engine = AlertEngine(AlertEngineConfig(
            poll_interval=int(os.getenv("ALERT_POLL_INTERVAL", "60")),
            batch_size=int(os.getenv("ALERT_BATCH_SIZE", "100")),
            dedup_window_hours=int(os.getenv("ALERT_DEDUP_HOURS", "24")),
            escalation_enabled=os.getenv("ALERT_ESCALATION_ENABLED", "true").lower() == "true",
            escalation_timeout_minutes=int(os.getenv("ALERT_ESCALATION_TIMEOUT", "30")),
        ))
        self._shutdown = asyncio.Event()

    async def run(self):
        """Run the alert worker."""
        logger.info("Starting alert worker...")
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        try:
            while not self._shutdown.is_set():
                try:
                    async with async_session_factory() as session:
                        # Process new events
                        stats = await self.engine.process_new_events(session)
                        
                        if stats.alerts_triggered > 0:
                            logger.info(
                                f"Processed {stats.events_processed} events, "
                                f"triggered {stats.alerts_triggered} alerts, "
                                f"sent {stats.notifications_sent} notifications"
                            )

                        # Check for escalations
                        escalated = await self.engine.check_escalations(session)
                        if escalated > 0:
                            logger.warning(f"Escalated {escalated} unacknowledged alerts")

                except Exception as e:
                    logger.error(f"Alert processing error: {e}", exc_info=True)

                # Wait for next poll or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=self.engine.config.poll_interval,
                    )
                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            logger.error(f"Alert worker crashed: {e}", exc_info=True)
            raise
        finally:
            logger.info("Alert worker stopped")

    def _handle_shutdown(self):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received")
        self._shutdown.set()


async def main():
    """Main entry point."""
    worker = AlertWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
