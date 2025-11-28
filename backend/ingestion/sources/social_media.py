"""Social media monitoring for crisis detection.

Monitors Twitter/X and Telegram for crisis-related content.
Uses public APIs and RSS bridges where available.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SocialPost:
    """Represents a social media post."""

    id: str
    platform: str  # twitter, telegram
    author: str
    content: str
    url: str
    posted_at: datetime
    engagement: int  # likes, retweets, views
    media_urls: list[str]
    hashtags: list[str]
    mentions: list[str]
    location: Optional[str]

    def to_event_dict(self) -> dict:
        """Convert to standard event dictionary format."""
        # Analyze content for category and threat level
        category, threat_level = self._analyze_content()

        # Calculate credibility based on engagement and source
        credibility = self._calculate_credibility()

        return {
            "title": self._generate_title(),
            "summary": self.content[:500],
            "category": category,
            "region": self.location,
            "source_url": f"https://{self.platform}.com",
            "link": self.url,
            "confidence": credibility,
            "published_at": self.posted_at.isoformat(),
            "threat_level": threat_level,
            "raw": f"{self.platform}:{self.id}",
        }

    def _generate_title(self) -> str:
        """Generate a title from content."""
        # Use first sentence or first 100 chars
        content = self.content.strip()
        
        # Remove URLs
        content = re.sub(r'https?://\S+', '', content)
        
        # Get first sentence
        sentences = re.split(r'[.!?]', content)
        if sentences:
            title = sentences[0].strip()[:100]
            if len(sentences[0]) > 100:
                title += "..."
            return title
        
        return content[:100] + "..." if len(content) > 100 else content

    def _analyze_content(self) -> tuple[str, str]:
        """Analyze content for category and threat level."""
        content_lower = self.content.lower()
        hashtags_lower = [h.lower() for h in self.hashtags]

        # Crisis keywords
        crisis_keywords = {
            "conflict": ["war", "attack", "bombing", "military", "troops", "fighting", "casualties"],
            "disaster:earthquake": ["earthquake", "quake", "tremor", "seismic"],
            "disaster:flood": ["flood", "flooding", "inundation", "deluge"],
            "disaster:storm": ["hurricane", "typhoon", "cyclone", "storm", "tornado"],
            "disaster:wildfire": ["wildfire", "fire", "blaze", "burning"],
            "health:outbreak": ["outbreak", "epidemic", "pandemic", "virus", "disease", "infection"],
            "humanitarian": ["refugees", "displaced", "humanitarian", "crisis", "famine", "hunger"],
            "terrorism": ["terrorist", "terrorism", "explosion", "bomb"],
        }

        # Determine category
        category = "social:unclassified"
        for cat, keywords in crisis_keywords.items():
            if any(kw in content_lower or kw in " ".join(hashtags_lower) for kw in keywords):
                category = cat
                break

        # Determine threat level
        threat_level = "low"
        
        high_urgency = ["breaking", "urgent", "emergency", "alert", "warning", "critical"]
        if any(word in content_lower for word in high_urgency):
            threat_level = "high"
        
        medium_urgency = ["reported", "confirmed", "update", "developing"]
        if threat_level == "low" and any(word in content_lower for word in medium_urgency):
            threat_level = "medium"

        # Boost threat level for high engagement
        if self.engagement > 10000:
            if threat_level == "low":
                threat_level = "medium"
            elif threat_level == "medium":
                threat_level = "high"

        return category, threat_level

    def _calculate_credibility(self) -> float:
        """Calculate credibility score."""
        score = 0.3  # Base score for social media

        # Boost for verified/official accounts (would need API data)
        # Boost for high engagement
        if self.engagement > 1000:
            score += 0.1
        if self.engagement > 10000:
            score += 0.1
        if self.engagement > 100000:
            score += 0.1

        # Boost for media attachments
        if self.media_urls:
            score += 0.1

        return min(score, 0.8)  # Cap at 0.8 for social media


@dataclass
class TwitterConfig:
    """Configuration for Twitter/X monitoring."""

    # Nitter instances for RSS (no API key needed)
    nitter_instances: list[str] = field(default_factory=lambda: [
        "nitter.net",
        "nitter.privacydev.net",
    ])
    
    # Accounts to monitor (crisis-focused)
    accounts: list[str] = field(default_factory=lambda: [
        "UN",
        "ABORGENPROJECT",
        "UNReliefChief",
        "WFP",
        "Aborgenproject",
        "ABORGENPROJECT",
        "ABORGENPROJECT",
        "ICABORGENPROJECT",
        "MSF",
        "WHO",
        "ABORGENPROJECT",
        "UNHCR",
        "UNICEF",
        "OABORGENPROJECT",
        "USABORGENPROJECT",
        "GDACS",
        "EMSR",
    ])
    
    # Search terms
    search_terms: list[str] = field(default_factory=lambda: [
        "breaking crisis",
        "humanitarian emergency",
        "earthquake damage",
        "flood emergency",
    ])
    
    timeout: float = 30.0
    max_posts_per_account: int = 10


@dataclass
class TelegramConfig:
    """Configuration for Telegram channel monitoring."""

    # Public channels to monitor (via RSS bridges)
    channels: list[str] = field(default_factory=lambda: [
        # Add public crisis monitoring channels
    ])
    
    # RSS bridge URL (self-hosted or public)
    rss_bridge_url: str = ""
    
    timeout: float = 30.0


class TwitterMonitor:
    """Monitor Twitter/X via Nitter RSS feeds."""

    def __init__(self, config: Optional[TwitterConfig] = None):
        self.config = config or TwitterConfig()
        self._client: httpx.AsyncClient | None = None
        self._current_instance_idx = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoodShepherd/1.0"},
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_nitter_instance(self) -> str:
        """Get next Nitter instance (round-robin)."""
        instance = self.config.nitter_instances[self._current_instance_idx]
        self._current_instance_idx = (self._current_instance_idx + 1) % len(self.config.nitter_instances)
        return instance

    async def fetch_posts(self) -> AsyncIterator[SocialPost]:
        """Fetch posts from monitored accounts."""
        client = await self._get_client()

        for account in self.config.accounts:
            try:
                async for post in self._fetch_account_posts(client, account):
                    yield post
            except Exception as e:
                logger.warning(f"Failed to fetch Twitter account @{account}: {e}")
                continue

            # Rate limiting
            await asyncio.sleep(1)

    async def _fetch_account_posts(
        self,
        client: httpx.AsyncClient,
        account: str,
    ) -> AsyncIterator[SocialPost]:
        """Fetch posts from a single account via Nitter RSS."""
        instance = self._get_nitter_instance()
        url = f"https://{instance}/{account}/rss"

        try:
            response = await client.get(url)
            
            if response.status_code == 404:
                logger.debug(f"Account @{account} not found on {instance}")
                return
            
            response.raise_for_status()

            # Parse RSS
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)

            count = 0
            for item in root.findall(".//item"):
                if count >= self.config.max_posts_per_account:
                    break

                post = self._parse_rss_item(item, account)
                if post:
                    yield post
                    count += 1

        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching @{account}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing @{account} feed: {e}")

    def _parse_rss_item(
        self,
        item,
        account: str,
    ) -> Optional[SocialPost]:
        """Parse RSS item into SocialPost."""
        from xml.etree import ElementTree

        def get_text(tag: str) -> str:
            elem = item.find(tag)
            return elem.text.strip() if elem is not None and elem.text else ""

        title = get_text("title")
        description = get_text("description")
        link = get_text("link")
        pub_date = get_text("pubDate")

        if not description:
            return None

        # Parse date
        try:
            posted_at = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
        except (ValueError, TypeError):
            posted_at = datetime.utcnow()

        # Extract post ID from link
        post_id = link.split("/")[-1].split("#")[0] if link else str(hash(description))

        # Extract hashtags and mentions
        hashtags = re.findall(r'#(\w+)', description)
        mentions = re.findall(r'@(\w+)', description)

        # Extract media URLs
        media_urls = re.findall(r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|mp4)', description)

        # Clean HTML from description
        clean_content = re.sub(r'<[^>]+>', '', description)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()

        return SocialPost(
            id=post_id,
            platform="twitter",
            author=account,
            content=clean_content,
            url=link,
            posted_at=posted_at,
            engagement=0,  # Not available via RSS
            media_urls=media_urls,
            hashtags=hashtags,
            mentions=mentions,
            location=None,
        )

    async def get_posts_as_dicts(self) -> list[dict]:
        """Fetch posts and return as list of dictionaries."""
        posts = []
        async for post in self.fetch_posts():
            posts.append(post.to_event_dict())
        return posts


class TelegramMonitor:
    """Monitor Telegram channels via RSS bridges."""

    def __init__(self, config: Optional[TelegramConfig] = None):
        self.config = config or TelegramConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={"User-Agent": "GoodShepherd/1.0"},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch_posts(self) -> AsyncIterator[SocialPost]:
        """Fetch posts from monitored Telegram channels."""
        if not self.config.rss_bridge_url or not self.config.channels:
            return

        client = await self._get_client()

        for channel in self.config.channels:
            try:
                async for post in self._fetch_channel_posts(client, channel):
                    yield post
            except Exception as e:
                logger.warning(f"Failed to fetch Telegram channel {channel}: {e}")
                continue

    async def _fetch_channel_posts(
        self,
        client: httpx.AsyncClient,
        channel: str,
    ) -> AsyncIterator[SocialPost]:
        """Fetch posts from a single Telegram channel."""
        # This would use an RSS bridge like https://github.com/RSS-Bridge/rss-bridge
        # with the Telegram bridge
        url = f"{self.config.rss_bridge_url}?action=display&bridge=Telegram&username={channel}&format=Atom"

        try:
            response = await client.get(url)
            response.raise_for_status()

            # Parse Atom feed
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)

            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall(".//atom:entry", ns):
                post = self._parse_atom_entry(entry, channel, ns)
                if post:
                    yield post

        except Exception as e:
            logger.warning(f"Error fetching Telegram channel {channel}: {e}")

    def _parse_atom_entry(
        self,
        entry,
        channel: str,
        ns: dict,
    ) -> Optional[SocialPost]:
        """Parse Atom entry into SocialPost."""

        def get_text(tag: str) -> str:
            elem = entry.find(f"atom:{tag}", ns)
            return elem.text.strip() if elem is not None and elem.text else ""

        content = get_text("content") or get_text("summary")
        if not content:
            return None

        # Clean HTML
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()

        link_elem = entry.find("atom:link", ns)
        link = link_elem.get("href", "") if link_elem is not None else ""

        # Parse date
        updated = get_text("updated") or get_text("published")
        try:
            posted_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            posted_at = datetime.utcnow()

        return SocialPost(
            id=get_text("id") or str(hash(content)),
            platform="telegram",
            author=channel,
            content=clean_content,
            url=link,
            posted_at=posted_at,
            engagement=0,
            media_urls=[],
            hashtags=re.findall(r'#(\w+)', clean_content),
            mentions=re.findall(r'@(\w+)', clean_content),
            location=None,
        )

    async def get_posts_as_dicts(self) -> list[dict]:
        """Fetch posts and return as list of dictionaries."""
        posts = []
        async for post in self.fetch_posts():
            posts.append(post.to_event_dict())
        return posts


class SocialMediaAggregator:
    """Aggregates posts from multiple social media sources."""

    def __init__(
        self,
        twitter_config: Optional[TwitterConfig] = None,
        telegram_config: Optional[TelegramConfig] = None,
    ):
        self.twitter = TwitterMonitor(twitter_config)
        self.telegram = TelegramMonitor(telegram_config)

    async def close(self) -> None:
        await self.twitter.close()
        await self.telegram.close()

    async def fetch_all_posts(self) -> list[dict]:
        """Fetch posts from all configured sources."""
        posts = []

        # Fetch Twitter posts
        try:
            twitter_posts = await self.twitter.get_posts_as_dicts()
            posts.extend(twitter_posts)
            logger.info(f"Fetched {len(twitter_posts)} Twitter posts")
        except Exception as e:
            logger.error(f"Twitter fetch failed: {e}")

        # Fetch Telegram posts
        try:
            telegram_posts = await self.telegram.get_posts_as_dicts()
            posts.extend(telegram_posts)
            logger.info(f"Fetched {len(telegram_posts)} Telegram posts")
        except Exception as e:
            logger.error(f"Telegram fetch failed: {e}")

        return posts


# Convenience function
async def fetch_social_media_events() -> list[dict]:
    """Fetch events from all social media sources."""
    aggregator = SocialMediaAggregator()
    try:
        return await aggregator.fetch_all_posts()
    finally:
        await aggregator.close()
