# The Good Shepherd

**Autonomous OSINT Intelligence Platform for Missionaries in Europe**

The Good Shepherd is a read-only, legally compliant intelligence platform that continuously ingests, enriches, and displays public information to give missionaries situational awareness of their operating environment.

## 🎯 Purpose

The platform provides missionaries with continuous awareness of:

- Neighborhood stability and public safety
- Protests & demonstrations
- Cultural and political shifts
- Legal changes affecting NGOs and churches
- Migration & community tensions
- Crime and public safety trends
- Infrastructure disruptions
- Health & environmental hazards
- Social sentiment trends

**Important:** This is a "pane of glass" for awareness, NOT a command & control system. The platform:
- ✅ Gathers and displays public intelligence (OSINT only)
- ✅ Provides visualizations, summaries, and insights
- ❌ Does NOT track private individuals
- ❌ Does NOT dispatch or direct real-world actions
- ❌ Does NOT perform intrusion or exploitation

## 📋 Architecture

### Backend
- **Framework:** FastAPI + Python 3.11
- **Database:** PostgreSQL 15 + PostGIS
- **Cache/Queue:** Redis
- **Migrations:** Alembic
- **Workers:** Celery/APScheduler for autonomous ingestion

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router
- **Mapping:** Leaflet + React-Leaflet
- **UI:** Clean, intuitive interface for non-technical users
- **Deployment:** Nginx (production-ready Docker setup)

### Key Components
- **Ingest Workers:** Autonomous fetching from RSS, APIs, social media
- **LLM Enrichment Layer:**
  - Entity extraction (locations, organizations, groups, topics, keywords)
  - Automatic summarization
  - Sentiment analysis
  - Automatic categorization
  - Confidence & relevance scoring
- **Intelligence Fusion:**
  - Event clustering and duplicate detection
  - Geospatial and temporal similarity
  - Multi-source fusion
  - Stability trend assessment
- **Event Model:** Categorized, geolocated intelligence events
- **Auth System:** Multi-tenant with organizations and roles

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ with PostGIS (if not using Docker)
- Redis (if not using Docker)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Goodshepherd
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Edit `.env` file**
   - Set `JWT_SECRET_KEY` to a secure random string
   - Set `OPENAI_API_KEY` if using OpenAI for LLM features
   - Adjust other settings as needed

4. **Start services**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

6. **Check health**
   ```bash
   curl http://localhost:8000/health
   ```

7. **Access the application**
   - Frontend: http://localhost (or http://localhost:80)
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development Setup

1. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis**
   ```bash
   # Use Docker for just the databases
   docker-compose up -d postgres redis
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start backend**
   ```bash
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --reload
   ```

6. **Run worker (in separate terminal)**
   ```bash
   python -m workers.rss_worker
   ```

## 🚀 Production Deployment

For production deployments, see the comprehensive [DEPLOYMENT.md](DEPLOYMENT.md) guide which covers:

- Docker and Kubernetes deployment
- Environment configuration
- Security best practices
- Monitoring and health checks
- Backup and recovery procedures
- Performance tuning
- Troubleshooting

**Quick Production Start:**
```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Access monitoring endpoints
curl https://yourdomain.com/monitoring/health/detailed
```

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Events
- `GET /events` - List events (with filters)
- `GET /events/{event_id}` - Get single event

### Dashboard
- `GET /dashboard/summary` - Dashboard summary with key metrics
- `GET /dashboard/trends` - Time-series trend analysis
- `GET /dashboard/category-analysis/{category}` - Category-specific analysis

### Dossiers & Watchlists
- `GET /dossiers` - List all dossiers
- `POST /dossiers` - Create new dossier
- `GET /dossiers/{id}` - Get dossier by ID
- `PATCH /dossiers/{id}` - Update dossier
- `DELETE /dossiers/{id}` - Delete dossier
- `GET /dossiers/{id}/stats` - Get dossier statistics
- `POST /dossiers/{id}/refresh` - Refresh dossier stats
- `GET /watchlists` - List all watchlists
- `POST /watchlists` - Create new watchlist

### Ingest & Fusion
- `POST /ingest/fusion/run` - Run clustering & fusion on recent events
- `GET /ingest/health` - Ingest subsystem health

### Event Feedback
- `POST /feedback/events/{event_id}` - Submit feedback on event quality
- `GET /feedback/events/{event_id}` - Get all feedback for an event
- `GET /feedback` - List feedback with filters (by event, user, rating)
- `DELETE /feedback/{feedback_id}` - Delete feedback entry

### Organization Settings
- `GET /settings` - Get organization settings (auto-creates if none exist)
- `PUT /settings` - Update organization settings (partial update)
- `POST /settings/reset` - Reset settings to defaults

### Audit Logs
- `GET /audit/logs` - Get audit logs with filtering and pagination
- `GET /audit/stats` - Get aggregate audit statistics

### Monitoring (Production)
- `GET /monitoring/health/live` - Liveness probe (Kubernetes)
- `GET /monitoring/health/ready` - Readiness probe (Kubernetes)
- `GET /monitoring/health/detailed` - Detailed health with components
- `GET /monitoring/metrics` - Application metrics
- `GET /monitoring/version` - Version information

### Health (Legacy)
- `GET /health` - Basic health check
- `GET /` - API info

## 🗃️ Database Schema

### Core Tables
- **users** - User accounts
- **organizations** - Multi-tenant organizations
- **user_organization** - User-org membership with roles
- **events** - Intelligence events with geolocation (GLOBAL)
- **sources** - Data source tracking

### Intelligence Tables
- **dossiers** - Tracked entities (location, org, group, topic, person) (ORG-SCOPED)
- **watchlists** - Collections of dossiers with priorities (ORG-SCOPED)
- **watchlist_dossier** - Many-to-many dossier-watchlist relationships

### Governance Tables
- **event_feedback** - User feedback on event quality and relevance (ORG-SCOPED)
- **audit_logs** - Comprehensive audit trail of all user actions (ORG-SCOPED)
- **organization_settings** - Per-tenant configuration and preferences (ORG-SCOPED)

### Multi-Tenant Architecture
- **GLOBAL objects:** Events and sources are shared across all organizations
- **ORG-SCOPED objects:** Dossiers, watchlists, feedback, audit logs, and settings are isolated per organization
- **See:** [docs/DATA_MODEL.md](docs/DATA_MODEL.md) for detailed multi-tenancy explanation

### Event Categories
- `protest` - Protests and demonstrations
- `crime` - Crime incidents
- `religious_freedom` - Religious freedom issues
- `cultural_tension` - Cultural tensions
- `political` - Political events
- `infrastructure` - Infrastructure disruptions
- `health` - Health alerts
- `migration` - Migration-related events
- `economic` - Economic events
- `weather` - Weather/natural disasters
- `community_event` - Community gatherings
- `other` - Uncategorized

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Auth
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM (OpenAI)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo-preview

# Worker Intervals
RSS_WORKER_INTERVAL_MINUTES=30
NEWS_WORKER_INTERVAL_MINUTES=60
```

## 🧪 Testing

Run tests with pytest:

```bash
cd backend
pytest
```

Run specific test file:
```bash
pytest tests/test_events_api.py
pytest tests/test_enrichment.py
```

Note: Enrichment tests will use fallback methods if no OpenAI API key is configured.

## 📊 Ingestion Sources

### ✅ Currently Live
- **RSS Feeds:** Fully operational with automatic enrichment
  - European news outlets
  - Government press releases
  - Crisis monitoring feeds
  - NGO updates

### 📋 Planned Sources
- **Government:** EU Home Affairs, Europol, UNHCR, WHO Europe
- **News APIs:** Reuters, AP, BBC, Politico Europe
- **Crisis Monitoring:** GDACS, MeteoAlarm, EMSC
- **NGO Feeds:** MSF, IRC, UN OCHA, Red Cross
- **Social Media (Public):** Twitter/X public search, Reddit, public Telegram

**For detailed ingestion status and implementation roadmap, see [docs/INGESTION.md](docs/INGESTION.md)**

## 🔐 Security & Privacy

### Hard Constraints
- ❌ No tracking of private individuals
- ❌ No facial recognition
- ❌ No scraping private accounts/groups
- ❌ No intrusion, scanning, or deanonymization
- ✅ Public officials and organizations may be named if in public sources
- ✅ Only public data with clear source attribution

## 📦 Project Structure

```
Goodshepherd/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── core/                 # Core modules (config, db, logging)
│   ├── models/               # SQLAlchemy models
│   ├── routers/              # FastAPI routers
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic services
│   ├── workers/              # Ingestion workers
│   ├── schedulers/           # Job schedulers
│   ├── tests/                # Test suite
│   ├── main.py               # FastAPI entrypoint
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React frontend (Phase 4+)
├── docker-compose.yml        # Docker orchestration
└── README.md                 # This file
```

## 🚧 Development Phases

### ✅ Phase 1: Foundation
- Backend skeleton with FastAPI
- Auth system (users, orgs, roles)
- Event model with categories
- Basic RSS worker
- Alembic migrations
- Docker setup

### ✅ Phase 2: Enrichment
- LLM client implementation (OpenAI)
- Entity extraction (locations, organizations, groups, topics, keywords)
- Automatic summarization (1-2 sentence neutral summaries)
- Sentiment analysis (positive/neutral/negative)
- Automatic categorization (12 event categories)
- Enrichment pipeline coordinator
- Confidence & relevance scoring
- Integration with RSS worker

### ✅ Phase 3: Intelligence Fusion
- Advanced scoring algorithms (confidence, relevance, priority)
- Event clustering (grouping similar events)
- Duplicate detection (same incident from multiple sources)
- Geospatial clustering (Haversine distance, location matching)
- Text similarity (Jaccard similarity)
- Event fusion (merging related events into unified view)
- Stability trend assessment
- Admin endpoint for triggering fusion (POST /ingest/fusion/run)

### ✅ Phase 4: Frontend - Stream View
- React 18 + TypeScript + Vite setup
- Tailwind CSS for styling
- Authentication UI (login/register pages)
- Protected routes with auth guards
- Event timeline/stream view with real-time updates
- Event cards with enriched data display
- Filtering system (category, sentiment, location, relevance)
- Event pagination and "Load More" functionality
- Expandable event details with full text and sources
- Multi-source event indicators
- Entity display (locations, organizations, topics)
- Responsive design with loading and error states
- Docker deployment configuration

### ✅ Phase 5: Frontend - Map View
- Interactive Leaflet map with OpenStreetMap tiles
- Geospatial event visualization with custom markers
- Color-coded markers by event category (12 distinct colors)
- Click-to-view event popups with full details
- Cluster indicators for multi-source events
- Auto-fitting map bounds to display all events
- Event count overlay and statistics
- Full filter integration (category, sentiment, location, relevance)
- Responsive map layout with legend
- Navigation between Stream and Map views
- Handles events without geolocation gracefully

### ✅ Phase 6: Dossiers & Watchlists
- Backend: Dossier and Watchlist models with full CRUD API
- Database migration: dossiers, watchlists, watchlist_dossier tables
- 5 dossier types: location, organization, group, topic, person (public officials only)
- Auto-tracking event statistics (counts, timestamps, 7d/30d trends)
- Smart entity matching across all entity types with alias support
- Detailed analytics: category distribution, sentiment analysis
- User-defined watchlists with priority levels (low/medium/high/critical)
- Many-to-many dossier-watchlist relationships
- Frontend: DossierCard, CreateDossierModal, Dossiers page
- React hooks: useDossiers, useWatchlists for state management
- Full UI for creating, viewing, editing, and deleting dossiers
- Search and filter dossiers by type and name
- Refresh stats manually or automatically
- OSINT compliant throughout (no private individual tracking)

### ✅ Phase 7: Dashboard
- Backend: Dashboard API endpoints (/dashboard/summary, /dashboard/trends)
- Real-time summary metrics (today, week, month event counts)
- High-relevance event tracking and highlighting
- Category distribution visualization (7-day period)
- Sentiment distribution analysis with percentages
- Top active locations with event counts
- Active vs total dossiers tracking
- Recent high-priority events feed (today's highlights)
- Trend analysis API with daily event counts
- Category trends over time (up to 90 days)
- Sentiment trends tracking
- Frontend: Dashboard page with "Today's Picture" view
- StatCard component for key metrics with trend indicators
- Visual progress bars for category distribution
- Sentiment breakdown with color-coded bars
- Top locations grid display
- Today's high-priority events list
- Responsive dashboard layout with 4-column grid
- Real-time data refresh capability

### ✅ Phase 8: Production Ready (Current)
- **Request Tracking & Logging:**
  - Structured logging with request IDs for tracing
  - JSON log format for machine parsing
  - Contextual logging with request metadata
  - Request/response timing and status tracking
- **Security Middleware:**
  - Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
  - Request tracking with unique IDs
  - CORS properly configured
- **Enhanced Monitoring:**
  - Detailed health checks (/monitoring/health/detailed)
  - Kubernetes-ready liveness probe (/monitoring/health/live)
  - Kubernetes-ready readiness probe (/monitoring/health/ready)
  - Application metrics endpoint (/monitoring/metrics)
  - Component-level health diagnostics
  - Database connection pool monitoring
  - Version information endpoint
- **Audit Trails & Governance:**
  - Comprehensive audit logging for all user actions
  - Track create/update/delete/view/export operations
  - IP address and user agent tracking for forensics
  - Audit log API with filtering and pagination (GET /audit/logs)
  - Aggregate statistics endpoint (GET /audit/stats)
  - Tamper-resistant audit trail with timestamps
  - Organization-scoped audit access control
- **Event Feedback System:**
  - User feedback collection on event quality and relevance
  - Accuracy ratings (1-5 stars) for LLM enrichment quality
  - Relevance ratings for content filtering improvement
  - False positive reporting mechanism
  - Category correction suggestions
  - Free-text feedback for detailed reports
  - Backend model and API endpoints for feedback CRUD
  - Used for continuous enrichment improvement
- **Tenant-Level Configuration:**
  - Organization settings model for per-tenant customization
  - Default filters (categories, sentiment, relevance threshold)
  - Alert thresholds and notification preferences
  - Feature toggles (email alerts, clustering, feedback, audit logging)
  - Display preferences (map zoom/center, events per page)
  - Data retention policies (event and audit log retention)
  - Regional focus (include/exclude specific regions)
  - Flexible JSON custom configuration field
  - Settings API with GET/PUT/reset endpoints
  - Auto-creation of default settings per organization
- **Risk Mitigation & Ethics:**
  - Comprehensive risk and misuse mitigation documentation
  - Detailed misuse scenario analysis with prevention strategies
  - Technical and organizational safeguards
  - Monitoring and auditing procedures
  - Incident response playbooks
  - Legal and compliance considerations
  - Ethical guidelines for OSINT-only, non-kinetic mission
- **Comprehensive Test Suite:**
  - Monitoring endpoint tests
  - Dashboard API tests
  - Dossier and watchlist tests
  - Event feedback functionality tests
  - Integration tests for all endpoints
  - Authentication and authorization tests
- **Production Documentation:**
  - Complete deployment guide (DEPLOYMENT.md)
  - Docker and Kubernetes deployment examples
  - Environment configuration guide
  - Security best practices
  - Backup and recovery procedures
  - Troubleshooting guide
  - Performance tuning recommendations
  - Risk mitigation and ethical safeguards guide (RISK_MITIGATION.md)
- **Production Features:**
  - Health checks for orchestration
  - Structured JSON logging
  - Request correlation IDs
  - Database connection pooling
  - Error tracking and reporting
  - Graceful shutdown handling

## 📚 Documentation

- **[Data Model & Multi-Tenancy](docs/DATA_MODEL.md)** - Understanding org-scoped vs global data
- **[Ingestion Sources](docs/INGESTION.md)** - Current sources and roadmap
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions
- **[Risk Mitigation & Ethics](docs/RISK_MITIGATION.md)** - Ethical safeguards and misuse prevention
- **[Audit Logging](docs/AUDIT_LOGGING.md)** - Comprehensive audit trail system
- **[Feedback System](docs/FEEDBACK_SYSTEM.md)** - Human feedback loop for quality improvement
- **[Organization Settings](docs/ORG_SETTINGS.md)** - Tenant-level configuration guide

## 📝 Contributing

This is a mission-critical platform. All contributions must:
1. Maintain OSINT-only principles
2. Include tests
3. Follow existing code style
4. Document new features

**Note:** This is a private, closed-source project. Contributions are accepted only from authorized developers.

## 📄 License

**Proprietary and Confidential**

This software is the proprietary and confidential property of The Good Shepherd Project. All rights reserved.

Unauthorized copying, distribution, modification, or use of this software is strictly prohibited. This software may only be used for authorized OSINT intelligence purposes and must not be used for tracking private individuals, intrusion, or any kinetic operations.

See [LICENSE](LICENSE) for full terms.

## 🙏 Credits

Built with care for missionaries serving in Europe.

## 🤖 LLM Enrichment

The platform uses AI to automatically enrich raw data:

**Entity Extraction:**
- Locations (cities, neighborhoods, countries)
- Organizations (agencies, NGOs, parties)
- Groups (protesters, residents, migrants)
- Topics (immigration, policy, religion)
- Keywords (key phrases)

**Automatic Categorization:**
12 categories: protest, crime, religious_freedom, cultural_tension, political, infrastructure, health, migration, economic, weather, community_event, other

**Sentiment Analysis:**
Positive, neutral, or negative classification

**Scoring:**
- **Confidence Score:** Based on text length, entity count, category specificity, source verification
- **Relevance Score:** Higher for safety-related events (crime, protest, health, religious freedom)
- **Priority Score:** Combines relevance, confidence, recency, and cluster size

**LLM Provider:**
- Primary: OpenAI (GPT-4 Turbo)
- Fallback: Basic keyword matching and rule-based analysis
- All methods include graceful degradation

## 🔗 Intelligence Fusion

The platform automatically detects and merges related events:

**Clustering Algorithm:**
- **Time Window:** Events within 24 hours can cluster
- **Location Matching:** Same city/neighborhood or within 50km
- **Category Match:** Same event category required
- **Text Similarity:** Jaccard similarity (0.6 threshold)

**Duplicate Detection:**
- Multiple sources reporting same incident
- Haversine distance for geospatial proximity
- Location name normalization and fuzzy matching
- Entity overlap analysis

**Event Fusion:**
- Merges multiple reports into unified view
- Combines source lists from all reports
- Merges entity lists (deduplicated)
- Uses best summary (highest confidence)
- Averages scores with multi-source boost
- Assesses stability trend over time

**Running Fusion:**
```bash
# Trigger fusion for events from last 24 hours
curl -X POST http://localhost:8000/ingest/fusion/run?hours_back=24 \
  -H "Authorization: Bearer <token>"
```

## 📋 Audit Trails & Governance

The platform includes comprehensive audit logging for accountability and compliance:

**What Gets Logged:**
- All create, update, delete, view, and export operations
- User ID and organization context
- IP address and user agent for forensics
- Action metadata (what changed, what was accessed)
- Timestamp for chronological tracking

**Audit Log API:**
```bash
# Get audit logs with filtering
GET /audit/logs?action_type=delete&days=30&page=1&page_size=50

# Get aggregate statistics
GET /audit/stats?days=7
```

**Use Cases:**
- Investigate suspicious activity patterns
- Compliance reporting and regulatory audits
- Incident response and forensics
- User activity monitoring by administrators
- Accountability for data modifications

## 🔄 Event Feedback System

Users can provide feedback on event quality to continuously improve LLM enrichment:

**Feedback Types:**
- **Accuracy Rating:** 1-5 stars for overall event accuracy
- **Relevance Rating:** 1-5 stars for event relevance to mission
- **False Positive:** Flag events that shouldn't have been ingested
- **Category Correction:** Suggest correct category if miscategorized
- **Free-text Feedback:** Detailed explanations and suggestions

**API Usage:**
```bash
# Submit feedback on an event
POST /feedback/events/{event_id}
{
  "accuracy_rating": 4,
  "relevance_rating": 5,
  "is_false_positive": false,
  "suggested_category": null,
  "feedback_text": "Good event, very relevant to our region"
}

# Get all feedback for an event
GET /feedback/events/{event_id}
```

**Benefits:**
- Continuously improve LLM enrichment accuracy
- Identify patterns in false positives
- Refine relevance scoring algorithms
- Collect user insights for better categorization

## ⚙️ Organization Settings

Each organization can customize platform behavior without code deployment:

**Configurable Settings:**

**Default Filters:**
- Default categories to display
- Default sentiment filter (positive/neutral/negative)
- Minimum relevance threshold (0.0-1.0)

**Alert Thresholds:**
- High-priority threshold for alerts
- Categories that trigger alerts
- Sentiment types that trigger alerts

**Feature Toggles:**
- Enable/disable email alerts
- Enable/disable event clustering
- Enable/disable feedback collection
- Enable/disable audit logging

**Display Preferences:**
- Default map zoom level and center coordinates
- Events per page in list views

**Data Retention:**
- Event retention days (auto-delete old events)
- Audit log retention days

**Regional Focus:**
- Focus regions (prioritize certain countries/areas)
- Exclude regions (completely filter out certain areas)

**API Usage:**
```bash
# Get organization settings
GET /settings

# Update settings (partial update)
PUT /settings
{
  "default_min_relevance": 0.7,
  "high_priority_threshold": 0.85,
  "exclude_regions": ["Asia", "Americas"]
}

# Reset to defaults
POST /settings/reset
```

---

**Version:** 0.8.0 (Phase 8 - Production Ready)
**Status:** Production Ready
