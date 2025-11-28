# Changelog

All notable changes to Good Shepherd will be documented in this file.

## [0.3.0] - 2025-11-26

### Added - Major Feature Release

#### Real-time Updates
- WebSocket server for live event broadcasting
- Connection manager with heartbeat and reconnection
- Client subscription filtering (by region, category, threat level)
- Frontend WebSocket hook with auto-reconnect

#### Offline-First PWA
- IndexedDB storage for events, reports, and alerts
- Service worker with intelligent caching strategies
- Background sync for offline actions
- Offline map tile caching

#### Mobile Missionary Dashboard
- Touch-optimized interface for field workers
- Quick "I'm Safe" check-in button
- Emergency contact integration
- Threat level summary banner
- Real-time alert toasts with vibration

#### SMS/WhatsApp Alerts (Twilio)
- Twilio integration for SMS delivery
- WhatsApp Business API support
- Recipient management with filters
- Priority-based message formatting

#### Additional Intelligence Sources
- **GDACS**: Global Disaster Alert and Coordination System
- **ACLED**: Armed Conflict Location & Event Data
- **State Dept**: US Travel Advisories

#### Geofencing & Location
- Circular and polygon geofence support
- User location tracking
- Enter/exit alerts for threat zones
- Nearby threat detection
- Event-to-geofence conversion

#### Reporting Enhancements
- PDF report generation
- Email digest service
- Daily/weekly scheduled digests
- HTML email templates

#### Production Readiness
- Rate limiting on public endpoints (slowapi)
- OpenTelemetry instrumentation for tracing
- Request logging middleware
- Load testing setup with Locust
- Docker healthchecks

### Changed
- API version bumped to 0.3.0
- Added CORS middleware for frontend
- Enhanced environment configuration
- Dynamic admin API key lookup for testing support
- Improved Dockerfiles with healthchecks and proper commands

### Documentation
- Comprehensive API documentation (`docs/API.md`)
- Feature guide (`docs/FEATURES.md`)
- Deployment guide (`docs/DEPLOYMENT.md`)
- Load testing README

---

## [0.2.0] - 2025-11-26

### Added
- MapLibre GL JS integration for map visualization
- Tailwind CSS for modern styling
- Lucide React icons
- Date-fns for date formatting
- Meilisearch client for full-text search
- Alembic for database migrations
- Comprehensive test dependencies (pytest, pytest-asyncio, pytest-cov)

### Changed
- Updated all Python dependencies to latest stable versions (Nov 2025)
  - FastAPI 0.115.5
  - Pydantic 2.10.2
  - SQLAlchemy 2.0.36
  - Redis 5.2.1
  - httpx 0.28.1
- Updated frontend to React 18.3.1 (stable) from React 19 RC
- Updated react-router-dom to v6.28.0
- Downgraded Express to 4.21.1 (stable) from 5.x beta
- Fixed Pydantic validators to use `@field_validator` (v2 API)
- Added missing `Report` and `SearchResponse` models to API

### Fixed
- Removed references to undefined scraper functions in rss-collector.js
- Fixed deprecated Pydantic `@validator` decorators

### Security
- Added `ADMIN_API_KEY` environment variable for protected endpoints

## [0.1.0] - Initial Release

### Added
- Core data ingestion pipeline (RSS feeds, web scraping)
- FastAPI backend with event processing
- React frontend with COP (Common Operational Picture) UI
- AI service for threat detection and translation
- Docker Compose infrastructure
- PostgreSQL + PostGIS for geospatial data
- Redis for event queuing
- Meilisearch for search indexing
- Alert rules system with CRUD API
- Situational report generation
- Geocoding via Nominatim
