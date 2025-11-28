"""Multi-source ingestion background worker.

Fetches data from all configured sources (GDACS, ReliefWeb, WHO, social media).
Run with: python -m backend.workers.ingestion_worker
"""

import asyncio
import logging
import os
import signal
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ingestion.multi_source_ingest import MultiSourceIngestionService, MultiSourceConfig

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionWorker:
    """Background worker for multi-source data ingestion."""

    def __init__(self):
        self.config = MultiSourceConfig.from_env()
        self.service = MultiSourceIngestionService(self.config)
        self._shutdown = asyncio.Event()

    async def run(self):
        """Run the ingestion worker."""
        logger.info("Starting ingestion worker...")
        
        # Log enabled sources
        sources = []
        if self.config.gdacs_enabled:
            sources.append("GDACS")
        if self.config.reliefweb_enabled:
            sources.append("ReliefWeb")
        if self.config.who_enabled:
            sources.append("WHO")
        if self.config.social_enabled:
            sources.append("Social Media")
        if self.config.acled_enabled:
            sources.append("ACLED")
        
        logger.info(f"Enabled sources: {', '.join(sources) or 'None'}")
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        try:
            await self.service.start()
        except Exception as e:
            logger.error(f"Ingestion worker crashed: {e}", exc_info=True)
            raise
        finally:
            await self.service.stop()
            logger.info("Ingestion worker stopped")

    def _handle_shutdown(self):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received")
        asyncio.create_task(self.service.stop())


async def main():
    """Main entry point."""
    worker = IngestionWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
