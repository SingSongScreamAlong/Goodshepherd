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

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Events
- `GET /events` - List events (with filters)
- `GET /events/{event_id}` - Get single event

### Ingest & Fusion
- `POST /ingest/fusion/run` - Run clustering & fusion on recent events
- `GET /ingest/health` - Ingest subsystem health

### Health
- `GET /health` - Health check
- `GET /` - API info

## 🗃️ Database Schema

### Tables
- **users** - User accounts
- **organizations** - Multi-tenant organizations
- **user_organization** - User-org membership with roles
- **events** - Intelligence events with geolocation
- **sources** - Data source tracking

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

### Phase 1-2 (Current)
- RSS feeds (configurable)
- Automatic enrichment with LLM analysis

### Phase 3+ (Planned)
- **Government:** EU Home Affairs, Europol, UNHCR, WHO
- **News:** Reuters, AP, BBC, Politico Europe
- **Crisis:** GDACS, MeteoAlarm, EMSC
- **NGO:** MSF, IRC, UN humanitarian feeds
- **Social:** Twitter/X public search, Reddit, public Telegram

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

### ✅ Phase 4: Frontend - Stream View (Current)
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

### 📋 Phase 5: Frontend - Map View
- Geospatial visualization
- Cluster display
- Interactive filtering

### 📋 Phase 6: Dossiers & Watchlists
- Living entity/location profiles
- User-defined watchlists

### 📋 Phase 7: Dashboard
- "Today's Picture" view
- Summary charts
- Key highlights

### 📋 Phase 8: Production Ready
- Comprehensive logging
- Metrics/monitoring
- Full test coverage
- Documentation

## 📝 Contributing

This is a mission-critical platform. All contributions must:
1. Maintain OSINT-only principles
2. Include tests
3. Follow existing code style
4. Document new features

## 📄 License

[License information to be added]

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

---

**Version:** 0.4.0 (Phase 4)
**Status:** Active Development
