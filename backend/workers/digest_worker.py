"""Digest service background worker.

Sends scheduled digest emails (hourly, daily, weekly).
Run with: python -m backend.workers.digest_worker
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.alerts.digest_service import DigestService
from backend.database.session import async_session_factory

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DigestWorker:
    """Background worker for sending digest emails."""

    def __init__(self):
        self.service = DigestService()
        self._shutdown = asyncio.Event()
        
        # Track last run times
        self._last_hourly = datetime.min
        self._last_daily = datetime.min
        self._last_weekly = datetime.min
        
        # Configurable times
        self.daily_hour = int(os.getenv("DIGEST_DAILY_HOUR", "8"))  # 8 AM
        self.weekly_day = int(os.getenv("DIGEST_WEEKLY_DAY", "0"))  # Monday

    async def run(self):
        """Run the digest worker."""
        logger.info("Starting digest worker...")
        
        if not self.service.is_configured:
            logger.warning("SMTP not configured - digest worker will idle")
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        try:
            while not self._shutdown.is_set():
                now = datetime.utcnow()
                
                try:
                    async with async_session_factory() as session:
                        # Check hourly digests (every hour)
                        if self._should_run_hourly(now):
                            logger.info("Running hourly digests...")
                            count = await self.service.generate_hourly_digests(session)
                            logger.info(f"Sent {count} hourly digests")
                            self._last_hourly = now

                        # Check daily digests (at configured hour)
                        if self._should_run_daily(now):
                            logger.info("Running daily digests...")
                            count = await self.service.generate_daily_digests(session)
                            logger.info(f"Sent {count} daily digests")
                            self._last_daily = now

                        # Check weekly digests (at configured day and hour)
                        if self._should_run_weekly(now):
                            logger.info("Running weekly digests...")
                            count = await self.service.generate_weekly_digests(session)
                            logger.info(f"Sent {count} weekly digests")
                            self._last_weekly = now

                except Exception as e:
                    logger.error(f"Digest processing error: {e}", exc_info=True)

                # Wait for next check (every 5 minutes)
                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=300,  # 5 minutes
                    )
                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            logger.error(f"Digest worker crashed: {e}", exc_info=True)
            raise
        finally:
            logger.info("Digest worker stopped")

    def _should_run_hourly(self, now: datetime) -> bool:
        """Check if hourly digest should run."""
        # Run if we haven't run this hour
        return (now - self._last_hourly) >= timedelta(hours=1)

    def _should_run_daily(self, now: datetime) -> bool:
        """Check if daily digest should run."""
        # Run at the configured hour if we haven't run today
        if now.hour != self.daily_hour:
            return False
        return (now - self._last_daily) >= timedelta(hours=20)  # Buffer

    def _should_run_weekly(self, now: datetime) -> bool:
        """Check if weekly digest should run."""
        # Run on configured day at configured hour
        if now.weekday() != self.weekly_day:
            return False
        if now.hour != self.daily_hour:
            return False
        return (now - self._last_weekly) >= timedelta(days=6)  # Buffer

    def _handle_shutdown(self):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received")
        self._shutdown.set()


async def main():
    """Main entry point."""
    worker = DigestWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
