# Good Shepherd

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Good Shepherd is a real-time threat intelligence and situational awareness platform for global missions and ministry work. It integrates OSINT data collection, AI-powered analysis, and dual dashboards for analysts and field missionaries.

## Features

- **Data Collection**: RSS feeds from global and European sources (BBC, Al Jazeera, Deutsche Welle, Euronews, Reuters Europe)
- **AI Integration**: Threat detection, scoring, and translation using Hugging Face models
- **Dual Dashboards**: 
  - Missionary UI: Mobile-first alerts with SMS simulation and offline support
  - Analyst UI: Full intelligence with search, filters, timeline, and human-in-loop tools
- **PWA Support**: Offline capabilities, caching, service worker, mobile-first design
- **European AOR**: Multilingual support, GDPR compliance, regional feeds, disinformation resilience
- **Real-time Processing**: Live data ingestion, AI processing, and alerting

## Architecture

The platform consists of 9 core layers as outlined in the architecture diagram:

- **Data Collection Layer**: RSS feeds, APIs, social media
- **Data Ingestion & Processing Layer**: ETL, language translation, geo-parsing
- **AI/ML Intelligence Layer**: Threat detection, predictive analytics, NER
- **Human-in-the-Loop Validation**: Analyst review and feedback
- **Alerting & Output Layer**: Dual dashboards
- **Security & Compliance Layer**: RBAC, encryption, GDPR
- **Automation & Orchestration Layer**: Scheduling, failover
- **Visualization & UI Layer**: Responsive interfaces
- **Integration APIs**: Webhooks, external integrations

Technical stack:
- **Backend**: Node.js (Express) for data ingestion and API
- **Frontend**: React.js with React Router for dual interfaces
- **AI Service**: Python (Flask) with Hugging Face Transformers
- **Data Flow**: RSS → AI Processing → Cached Storage → Dashboards

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for production mode)

### Development Mode (No Docker)
```bash
./scripts/dev.sh
```
Uses SQLite - perfect for testing and development.

### Production Mode (With Docker)
```bash
./scripts/quickstart.sh
```
Uses PostgreSQL, Redis, Meilisearch via Docker.

This will:
1. Start infrastructure (Redis, PostgreSQL, Meilisearch)
2. Install Python and Node dependencies
3. Initialize the database
4. Start the backend API (port 8000)
5. Start the frontend (port 3000)

### Manual Setup

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/SingSongScreamAlong/Goodshepherd.git
   cd Goodshepherd
   cp infrastructure/.env.example infrastructure/.env
   ```

2. **Start infrastructure services:**
   ```bash
   cd infrastructure
   docker compose up -d redis postgres meilisearch
   cd ..
   ```

3. **Setup Python backend:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Start backend API:**
   ```bash
   source venv/bin/activate
   uvicorn backend.processing.api_main:app --reload --port 8000
   ```

6. **Start frontend (new terminal):**
   ```bash
   cd frontend
   npm start
   ```

### Access Points
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Meilisearch | http://localhost:7700 |

### Stop Services
```bash
./scripts/stop.sh
```

### Navigation
- **Missionary Dashboard**: http://localhost:3000/ (mobile alerts, offline support)
- **Analyst Dashboard**: http://localhost:3000/analyst (full intelligence interface)

## API Endpoints

### Backend (Port 3001)
- `GET /api/rss`: Fetches processed RSS data with AI threat levels

### AI Service (Port 5000)
- `POST /detect_threat`: Analyzes text for threat level
  - Body: `{"text": "sample text"}`
  - Response: `{"threat_level": "high", "confidence": 0.95, "original_label": "LABEL_0"}`
- `POST /translate`: Translates text between languages
  - Body: `{"text": "Hello", "source_lang": "en", "target_lang": "fr"}`
  - Response: `{"translated_text": "Bonjour"}`
- `POST /score_severity`: Scores severity based on keywords
  - Body: `{"text": "Crisis in Europe"}`
  - Response: `{"severity": "high", "threat_count": 1}`
- `GET /health`: Health check

## Configuration

- **RSS Feeds**: Edit `backend/rss-collector.js` to add/remove sources
- **AI Models**: Modify `ai_service/app.py` for different models
- **PWA**: Manifest in `frontend/public/manifest.json`
- **Environment**: Add API keys for production deployment

## Deployment

### Docker (Recommended)
```bash
# Build images
docker build -t good-shepherd-backend ./backend
docker build -t good-shepherd-frontend ./frontend
docker build -t good-shepherd-ai ./ai_service

# Run containers
docker-compose up
```

### Cloud Deployment
- **AWS/GCP/Azure**: Containerize services, deploy to cloud run
- **Database**: Add PostgreSQL for persistence
- **CDN**: Use for asset delivery
- **Monitoring**: Add logging and alerting

## Security & Compliance

- **GDPR**: Automatic anonymization, data minimization
- **Encryption**: End-to-end for data transmission
- **RBAC**: Role-based access (analyst vs missionary)
- **Audit Logging**: Full traceability

## Testing

- **Unit Tests**: Run `npm test` in frontend/backend
- **Integration**: Test API endpoints with Postman
- **E2E**: Manual testing of dashboards

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Roadmap

### Completed
- [x] MVP Build (data pipeline + missionary UI)
- [x] AI Integration (threat detection + translation)
- [x] Analyst Dashboard (full visualization)
- [x] Field Deployment (PWA + offline)
- [x] European AOR Pilot (regional feeds + compliance)
- [x] Alert rules CRUD API with admin authentication
- [x] Situational report generation
- [x] Event verification and credibility scoring

### In Progress (v0.3.0)
- [ ] MapLibre map visualization in frontend
- [ ] Real-time WebSocket updates
- [ ] Matrix/SMTP alert delivery

### Future Enhancements
- Additional data sources (APIs, social media)
- Advanced AI models (predictive analytics)
- Real SMS integration via Twilio
- Multi-language UI
- Kubernetes deployment
- Mobile app (React Native)

## License

MIT License - see LICENSE file for details

## Support

For questions or issues, please open a GitHub issue or contact the development team.

---

**Good Shepherd**: Shepherding missions with intelligence and awareness.
