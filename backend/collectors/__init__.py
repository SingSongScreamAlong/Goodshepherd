"""Collector package for data ingestion."""
from .collector_base import CollectorBase
from .rss_collector import RSSCollector
from .official_collector import OfficialCollector
from .news_collector import NewsCollector
from .orchestrator import CollectorOrchestrator, collector_orchestrator, run_collection

__all__ = [
    "CollectorBase",
    "RSSCollector",
    "OfficialCollector",
    "NewsCollector",
    "CollectorOrchestrator",
    "collector_orchestrator",
    "run_collection",
]

