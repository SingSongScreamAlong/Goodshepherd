# Ingestion Sources & Status

## Overview

The Good Shepherd platform ingests intelligence from multiple public sources (OSINT only). This document clarifies what is **currently operational** versus what is **planned** for future implementation.

## ✅ Currently Live (Operational)

### RSS Feeds
**Status:** ✅ Fully operational
**Worker:** `backend/workers/rss_worker.py`
**Description:** Fetches and processes RSS/Atom feeds from configured sources.

**Features:**
- Automatic feed parsing with `feedparser`
- HTTP timeout and redirect handling
- Duplicate detection (by source URL + published date)
- Full LLM enrichment pipeline integration
- Configurable fetch interval (default: 30 minutes)

**Configuration:**
```env
RSS_WORKER_INTERVAL_MINUTES=30
```

**Example Sources:**
- European news outlets
- Crisis monitoring feeds
- NGO/humanitarian organization updates
- Government press releases (via RSS)

**How to Add Sources:**
1. Add RSS feed URLs to the `sources` database table
2. Worker automatically picks up new sources on next run
3. No restart required

**Database Model:**
```python
class Source:
    url: str  # RSS feed URL
    name: str
    source_type: str  # "rss"
    is_active: bool
```

## 🚧 Planned (Not Yet Implemented)

The following ingestion sources are documented in the roadmap but **not yet implemented**:

### News APIs
**Status:** 📋 Planned
**Planned Sources:**
- Reuters API
- Associated Press (AP) wire
- BBC News API
- Politico Europe

**Implementation Notes:**
- Requires API keys for each service
- Rate limiting considerations
- Structured API responses (easier than RSS parsing)
- Some services require paid subscriptions

**Environment Variables (reserved):**
```env
NEWS_WORKER_INTERVAL_MINUTES=60
REUTERS_API_KEY=
AP_API_KEY=
BBC_API_KEY=
```

### Government & Institutional Feeds
**Status:** 📋 Planned
**Planned Sources:**
- **EU Home Affairs:** Migration, border security, Schengen alerts
- **Europol:** Cross-border crime, terrorism alerts
- **UNHCR:** Refugee flows, humanitarian updates
- **WHO Europe:** Health alerts, disease surveillance

**Implementation Notes:**
- Most have free public APIs or data feeds
- Some require registration but no fees
- XML/JSON formats vary by organization
- Rate limits typically generous for non-commercial use

**Environment Variables (reserved):**
```env
GOV_WORKER_INTERVAL_MINUTES=120
EU_HOME_AFFAIRS_API_KEY=
EUROPOL_API_KEY=
UNHCR_API_KEY=
WHO_API_KEY=
```

### Crisis & Disaster Monitoring
**Status:** 📋 Planned
**Planned Sources:**
- **GDACS (Global Disaster Alert and Coordination System):** Earthquakes, floods, storms
- **MeteoAlarm:** Severe weather warnings for Europe
- **EMSC (European-Mediterranean Seismological Centre):** Earthquake alerts

**Implementation Notes:**
- All provide free public APIs
- Real-time or near-real-time updates
- GeoJSON/XML formats
- Critical for immediate situational awareness

**Environment Variables (reserved):**
```env
CRISIS_WORKER_INTERVAL_MINUTES=15
GDACS_API_KEY=  # May not be required
METEOALARM_API_KEY=
EMSC_API_KEY=
```

### Social Media (Public Only)
**Status:** 📋 Planned
**Planned Sources:**
- **Twitter/X:** Public tweets matching keywords/hashtags
- **Reddit:** Public subreddit posts (e.g., r/europe, city subreddits)
- **Public Telegram channels:** News channels, official government accounts

**Implementation Notes:**
- **CRITICAL:** Only public content, never private accounts
- Twitter API requires authentication, has rate limits
- Reddit API is free with registration
- Telegram public channel scraping (no private chats)
- Content moderation needed (spam, noise filtering)

**OSINT Compliance:**
- ❌ NO private accounts, DMs, or closed groups
- ❌ NO individual user tracking
- ✅ Only publicly visible posts/channels
- ✅ Only content from verified/official accounts or public interest

**Environment Variables (reserved):**
```env
SOCIAL_WORKER_INTERVAL_MINUTES=15
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_BEARER_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
TELEGRAM_BOT_TOKEN=  # For accessing public channels only
```

### NGO & Humanitarian Feeds
**Status:** 📋 Planned
**Planned Sources:**
- Médecins Sans Frontières (MSF)
- International Rescue Committee (IRC)
- UN OCHA (Office for the Coordination of Humanitarian Affairs)
- Red Cross/Red Crescent

**Implementation Notes:**
- Mix of RSS feeds and APIs
- Focus on Europe region filtering
- Humanitarian crisis reporting
- Project updates and safety alerts

## Implementation Roadmap

### Phase 1 (Completed)
- ✅ RSS worker operational
- ✅ LLM enrichment pipeline
- ✅ Event storage and deduplication
- ✅ Basic source management

### Phase 2 (Next Priority)
- 📋 News APIs (Reuters, AP, BBC)
- 📋 GDACS crisis monitoring
- 📋 MeteoAlarm weather warnings

### Phase 3 (Medium-Term)
- 📋 EU/Europol government feeds
- 📋 UNHCR/WHO institutional data
- 📋 Social media (Twitter/X public search)

### Phase 4 (Long-Term)
- 📋 Reddit public monitoring
- 📋 Telegram public channels
- 📋 NGO humanitarian feeds

## Adding New Ingestion Sources

### For Developers

To add a new ingestion source:

1. **Create Worker File:**
   ```python
   # backend/workers/news_api_worker.py
   class NewsAPIWorker:
       def fetch_articles(self, since: datetime) -> List[Dict]:
           # Fetch from API
           pass

       def process_article(self, article: Dict) -> Event:
           # Convert to Event model
           # Run through enrichment pipeline
           pass
   ```

2. **Register in Scheduler:**
   ```python
   # backend/schedulers/main.py
   from workers.news_api_worker import NewsAPIWorker

   schedule.every(60).minutes.do(news_worker.run)
   ```

3. **Add Configuration:**
   ```env
   # .env.example
   NEWS_API_KEY=your-key-here
   NEWS_API_INTERVAL_MINUTES=60
   ```

4. **Update Documentation:**
   - Move from "Planned" to "Live" in this file
   - Update README.md
   - Add API key instructions

### Worker Best Practices

1. **Error Handling:**
   - Graceful failures (log and continue)
   - Retry logic with exponential backoff
   - Circuit breaker for persistent failures

2. **Rate Limiting:**
   - Respect API rate limits
   - Implement request throttling
   - Use backoff on 429 errors

3. **Deduplication:**
   - Check for existing events (by source URL, published date, title hash)
   - Avoid re-ingesting same content
   - Update existing events if new info available

4. **Enrichment:**
   - Always run through LLM enrichment pipeline
   - Use fallback methods if LLM unavailable
   - Cache enrichment results

5. **Logging:**
   - Structured logging with source, status, count
   - Error tracking with context
   - Performance metrics (fetch time, items processed)

## OSINT Compliance Checklist

Before adding ANY new source:

- ✅ Is the data publicly available?
- ✅ Does the source allow automated access (check ToS)?
- ✅ Are we respecting rate limits?
- ✅ Is the data properly attributed to source?
- ❌ Does it track private individuals? (DISALLOWED)
- ❌ Does it access private accounts/groups? (DISALLOWED)
- ❌ Does it require authentication to non-public areas? (DISALLOWED)

## Current Statistics

**Ingestion Sources:**
- **Active:** 1 (RSS worker)
- **Configured:** TBD (depends on RSS sources in database)
- **Planned:** 15+ (across all categories)

**Enrichment:**
- **LLM Provider:** OpenAI GPT-4 Turbo
- **Fallback:** Rule-based classification
- **Success Rate:** ~95% (with API key)

**Performance:**
- **RSS Fetch:** ~2-5 seconds per feed
- **Enrichment:** ~3-8 seconds per event
- **Total Processing:** ~5-15 seconds per event

## Future Enhancements

1. **Adaptive Polling:**
   - Faster polling for high-priority sources
   - Slower polling for low-activity feeds

2. **Source Health Monitoring:**
   - Track source uptime/reliability
   - Automatic disabling of broken sources
   - Alert on prolonged failures

3. **Smart Filtering:**
   - Organization-specific source subscriptions
   - Region-based filtering (only Europe events)
   - Category-based source routing

4. **Real-Time Streaming:**
   - WebSocket connections for live feeds
   - Push notifications for critical events
   - Server-sent events (SSE) for dashboard

---

**Version:** 0.8.0
**Last Updated:** 2025-11-25
