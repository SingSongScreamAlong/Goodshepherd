# Good Shepherd Project Bible

## 1. Vision
Provide missionaries in Europe with a near-zero-cost, lawful situational awareness and early warning platform.

- Live common operational picture (COP) on a map.
- Free, open data only (RSS, public advisories, OSM, Copernicus, GDACS).
- Low overhead: one DigitalOcean droplet (~$15–20/mo).
- Outputs: daily SITREPs, push/email alerts, safe routes, and check-in workflows.

## 2. Core Outcomes
- **Operational Picture (COP)**: Map view of hazards/incidents across AOR.
- **Early Warning Alerts**: Threshold-based notifications (geo-fenced).
- **Mission Safety Workflows**: Check-ins, panic button, safe routes.
- **Situational Reports (SITREPs)**: Daily/weekly intel briefs (auto-drafted, analyst-edited).

## 3. Primary Intelligence Requirements
- **Physical Security**: Protests/unrest, violent incidents.
- **Disasters**: Earthquakes, floods, storms, fires, industrial accidents.
- **Health**: Outbreaks, health advisories.
- **Political/Legal**: Sudden changes affecting visas/religious activity.
- **Infrastructure**: Transport strikes, outages.

## 4. Data Sources (Free / OSINT Only)
- **Disasters**: GDACS RSS, USGS/EMSC quakes, Copernicus EMS.
- **Advisories**: US State Dept, UK FCDO, Canada RSS.
- **Weather/Env**: National met RSS, OpenWeatherMap free tier, OpenAQ.
- **Media**: Reuters, BBC, AFP, DW, local outlets via RSS.
- **Community**: Ushahidi/HOT OSM, local radio streams.
- **Geodata**: OpenStreetMap + Nominatim (self-host).

## 5. System Architecture
### Services (Docker Compose on single VPS)
- **Redis Streams** — event queue.
- **Postgres + PostGIS** — storage & geospatial.
- **Meilisearch** — search/index for events.
- **MinIO** — S3-compatible object storage.
- **Worker (Python)** — ingestion + enrichment.
- **API (FastAPI)** — health, search, alerts.
- **Frontend (React + MapLibre)** — map COP.
- **Caddy** — TLS reverse proxy with Let’s Encrypt.

### Workflow
1. Ingest (RSS/advisories) → Redis stream.
2. Process (geoparse, normalize, verify) → Postgres + Meilisearch.
3. Expose via FastAPI (`/api/search`, `/api/reports`).
4. Visualize in React/MapLibre frontend.
5. Notify (Matrix/SMTP alerts coming in Phase 2).

## 6. Code Modules
- `backend/utils/queue.py` → Redis helpers.
- `backend/ingestion/ingest_service.py` → RSS ingestion loop.
- `backend/processing/event_processor.py` → consume, geoparse, verify, store, index.
- `backend/processing/verification.py` → credibility scoring + threat heuristics.
- `backend/reporting/` → SITREP builder (`sitrep_builder.py`) and orchestration (`service.py`).
- `backend/geocode/` → Nominatim client.
- `backend/search/` → Meilisearch client wrapper.
- `backend/database/repository.py` → persistence & verification overrides.
- `frontend/src/App.js` → COP UI with verification + report panels.
- `infrastructure/docker-compose.yml` → stack definition.
- `infrastructure/Caddyfile` → reverse proxy TLS configuration.

## 7. Analyst Workflows
### 7.1 Event Verification Loop
- Pull latest events from `/api/search` or the COP UI (`frontend/src/App.js`).
- Review `verification_status`, `credibility_score`, `threat_level`, and `duplicate_of` metadata emitted by `backend/processing/event_processor.py`.
- Override or confirm assessments via forthcoming analyst endpoints (Phase 2); meanwhile use repository helper `update_event_verification()` inside `backend/database/repository.py` for manual adjustments.
- Tag verified, high-threat incidents for immediate alerting.

### 7.2 Situation Report Production
- Trigger auto-draft via `POST /api/reports/generate` handled by `backend/reporting/service.py`.
- Review generated summary/content in the COP `ReportList` sidebar (`frontend/src/App.js`).
- Copy into mission SITREP templates, add qualitative context, attach supporting graphics, archive final PDFs to MinIO.
- Record distribution list, publish timestamp, and report ID for audit trail.

### 7.3 Alert & Follow-up Checklist
- For events with `threat_level` ≥ medium, verify affected field teams and locations.
- Launch alerts through Matrix/SMTP (integration planned) and log actions in the ops tracker.
- Update check-in status, safe-movement guidance, and follow-up tasks based on SITREP outcomes.

### 7.4 Daily Rhythm
- **Morning (0900 CET)**: Generate daily SITREP, review overnight alerts, confirm feed health.
- **Noon**: Midday sweep of events, validate auto-verification results, adjust confidence scores if needed.
- **Evening**: Prepare overnight monitoring notes, rotate on-duty analyst, queue pending alerts.

### 7.5 Alert Configuration Preview
- Use `GET /api/alerts/evaluate` to preview which events match default alert rules (no side effects).
- Rules currently ship with two presets: `High Threat Europe` (critical, high threat in EU) and `Violence` (medium threat or higher violent categories).
- Alert engine relies on metadata produced by `backend/processing/event_processor.py` (`verification_status`, `threat_level`, `credibility_score`).
- Delivery sinks (`backend/alerts/delivery.py`) include logging, Matrix, and SMTP placeholders pending credential wiring.
- Planned automation (Phase 2) will persist rule configuration in Postgres and expose CRUD endpoints for analysts.

### 7.6 Managing Alert Rules
- Use the new `/api/alerts/rules` endpoints to manage alert configuration:
  - `GET /api/alerts/rules` lists stored rules (falls back to defaults when empty).
  - `POST /api/alerts/rules` creates a rule (requires `name`, `minimum_threat`, `minimum_credibility`, `priority`).
  - `PUT /api/alerts/rules/{id}` updates selected fields while validating threat and credibility bounds.
  - `DELETE /api/alerts/rules/{id}` removes a rule.
- Rule definitions persist via `AlertRuleRecord` (`backend/database/models.py`) and repository helpers in `backend/database/repository.py`.
- Protect mutations using `ADMIN_API_KEY`; supply `X-Admin-API-Key: <key>` when calling POST/PUT/DELETE.
- Frontend/console workflow roadmap: build analyst UI for CRUD actions (Phase 3) and integrate audit logging (future work).

### 7.7 Analyst UI Panel
- The COP sidebar (`frontend/src/App.js`) now includes an **Alert rules** panel listing stored configurations, showing thresholds and filtering metadata.
- Analysts can enter the admin key in the panel to enable create/update/delete actions without leaving the UI.
- Form fields map directly to the API payload (threat, credibility, lookback, priority, regions/categories, auto-ack).
- Successful actions refresh the list immediately; errors surface inline for rapid troubleshooting.

## 8. Deployment (DigitalOcean Droplet)
```
ssh ops@droplet
unzip good_shepherd_repo.zip -d good_shepherd && cd good_shepherd/good_shepherd_repo/infrastructure
docker compose build
docker compose up -d
```

- UI: `https://yourdomain.com`
- API: `https://yourdomain.com/api/search?q=athens`

## 9. MVP Timeline (90 Days)
- **Weeks 1–3**: Stand up infra, ingest GDACS/USGS/FCDO.
- **Weeks 4–6**: Worker enrichment (geoparse, verification, dedupe), Meilisearch integration.
- **Weeks 7–9**: Alerts (geo-fence rules), Matrix/SMTP integration.
- **Weeks 10–12**: Frontend COP with markers; daily SITREP generation.

## 10. Stretch Goals (Phase 2–3)
- **Offline mobile app** (React Native).
- **Route safety overlays** (OSM graph + hazard zones).
- **Image/video verification** module.
- **Partner data exchange** (STIX/TAXII).

## 11. Non-Goals
- No covert scraping, hacking, or private comms interception.
- No commercial feeds (Dataminr, Maxar, etc.).
- No tracking individuals without consent.

## 12. Deliverables to Windsurf
```
good_shepherd_repo/
  backend/...
  frontend/...
  infrastructure/...
  docs/...
```
- `docs/Blueprint.md` with vision + architecture.
- Compose & Caddyfile to deploy.
- Python + React code skeletons (ready to extend).
- `docs/Runbook.md`: one-page ops manual.

## 13. Tasks for Windsurf (Next Sprints)
- **Expand ingestion** to more RSS/advisories.
- **Implement stronger geoparser** (mordecai/OSM gazetteer).
- **Add clustering/deduplication** (underway via verification pipeline).
- **Wire frontend** to show live event pins from API.
- **Add analyst console** (filters, timeline, export SITREP).
- **Add push/email integration** (Matrix/SMTP).

## 14. Risks & Mitigations
- **Feed downtime** → multiple sources per hazard type.
- **False positives** → credibility scoring + human analyst oversight.
- **Privacy/GDPR** → no PII, store minimal data, publish collection policy.
- **Infra limits** → optimize for 1 VPS, scale later with K8s.
- **Alert fatigue** → tiered priorities, auto-ack rules, and analytics dashboards (Grafana) to monitor response times.

## 15. Budget & Sustainability
- **Hosting**: $15/mo DigitalOcean droplet.
- **Domain**: ~$1/mo.
- **Email/Matrix**: free/self-host.
- **Total**: ~$20/mo.

---
✅ This document + repo = everything Windsurf needs to keep coding and extending.
