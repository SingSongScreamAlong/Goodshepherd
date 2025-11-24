"""
RSS worker for ingesting public RSS feeds.
Continuously fetches RSS feeds from configured sources.
"""
import feedparser
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from backend.core.logging import get_logger
from backend.core.database import SessionLocal
from backend.models.source import Source
from backend.models.event import Event, EventCategory

logger = get_logger(__name__)


class RSSWorker:
    """Worker for fetching and processing RSS feeds."""

    def __init__(self):
        self.timeout = 30
        self.user_agent = "GoodShepherd/1.0 (OSINT Intelligence Platform)"

    def fetch_feed(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch RSS feed from URL.

        Args:
            url: RSS feed URL

        Returns:
            Parsed feed data or None if error
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = httpx.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning("Feed parsing warning", url=url, error=str(feed.bozo_exception))

            return feed

        except httpx.HTTPError as e:
            logger.error("HTTP error fetching feed", url=url, error=str(e))
            return None
        except Exception as e:
            logger.error("Error fetching feed", url=url, error=str(e))
            return None

    def process_feed_entry(self, entry: Dict[str, Any], source_name: str) -> Optional[Dict[str, Any]]:
        """
        Process a single RSS feed entry into event data.

        Args:
            entry: Feed entry dictionary
            source_name: Name of the source

        Returns:
            Event data dictionary or None
        """
        try:
            # Extract basic fields
            title = entry.get("title", "Untitled")
            summary = entry.get("summary", entry.get("description", ""))
            link = entry.get("link", "")

            # Parse timestamp
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_parsed:
                timestamp = datetime(*published_parsed[:6])
            else:
                timestamp = datetime.utcnow()

            # Build full text
            full_text = f"{title}\n\n{summary}"

            # Create event data
            event_data = {
                "timestamp": timestamp,
                "summary": title[:500],  # Limit to 500 chars
                "full_text": full_text,
                "category": EventCategory.OTHER,  # Default category, will be enriched later
                "source_list": [
                    {
                        "name": source_name,
                        "url": link,
                        "fetched_at": datetime.utcnow().isoformat()
                    }
                ],
                "confidence_score": 0.5,  # Default confidence
            }

            return event_data

        except Exception as e:
            logger.error("Error processing feed entry", source=source_name, error=str(e))
            return None

    def ingest_source(self, source: Source) -> int:
        """
        Ingest events from a single RSS source.

        Args:
            source: Source object from database

        Returns:
            Number of events created
        """
        logger.info("Ingesting RSS source", source_id=str(source.id), name=source.name, url=source.url)

        db = SessionLocal()
        events_created = 0

        try:
            # Update source last fetch time
            source.last_fetch_at = datetime.utcnow()

            # Fetch feed
            feed = self.fetch_feed(source.url)

            if not feed:
                source.error_count += 1
                source.last_error = "Failed to fetch feed"
                db.commit()
                return 0

            # Process entries
            for entry in feed.entries[:20]:  # Limit to 20 most recent entries
                event_data = self.process_feed_entry(entry, source.name)

                if event_data:
                    # Create event
                    event = Event(**event_data)
                    db.add(event)
                    events_created += 1

            # Update source success stats
            source.fetch_count += 1
            source.last_success_at = datetime.utcnow()
            source.last_error = None

            db.commit()

            logger.info(
                "RSS ingestion complete",
                source_id=str(source.id),
                source_name=source.name,
                events_created=events_created
            )

            return events_created

        except Exception as e:
            db.rollback()
            source.error_count += 1
            source.last_error = str(e)
            db.commit()
            logger.error("Error ingesting RSS source", source_id=str(source.id), error=str(e))
            return 0

        finally:
            db.close()

    def run(self):
        """
        Run RSS worker to ingest all active RSS sources.
        """
        logger.info("RSS worker starting")

        db = SessionLocal()

        try:
            # Get all active RSS sources
            sources = db.query(Source).filter(
                Source.is_active == True,
                Source.source_type == "rss"
            ).all()

            logger.info("Found RSS sources", count=len(sources))

            total_events = 0
            for source in sources:
                events_count = self.ingest_source(source)
                total_events += events_count

            logger.info("RSS worker completed", total_events=total_events)

        except Exception as e:
            logger.error("RSS worker error", error=str(e))

        finally:
            db.close()


def run_rss_worker():
    """Entry point for running RSS worker."""
    worker = RSSWorker()
    worker.run()


if __name__ == "__main__":
    # For testing
    run_rss_worker()
