# World Situational Awareness Architecture

This document describes the World Situational Awareness extensions built on top of The Good Shepherd platform.

## Overview

The World Situational Awareness system transforms Good Shepherd from a feed reader into a **Live Operational Picture** platform. It continuously collects open-source global data, verifies and confidence-scores information, and generates leadership-ready reports.

## Core Principles

### OSINT Only
- Ingests only publicly accessible data
- No private accounts, paywalls, or closed groups
- No tracking, fake identities, or interaction with platforms

### Transparency
- Every claim shows confidence (0-100%) and provenance
- Social media posts treated as UNVERIFIED CLAIMS until corroborated
- Full audit trail for verification decisions

### Models Regions, Not People
- Tracks geographic regions with continuously updated states
- Multi-dimensional scoring: physical, migration, security, socioeconomic, information reliability
- Output is a LIVE OPERATIONAL PICTURE

## New Data Models

### Source Extensions (`backend/models/source.py`)
- `trust_baseline` (0-100): Default trust level for source
- `source_type`: OFFICIAL, NEWS, SOCIAL, NGO, PARTNER
- `allowed_collection_method`: API, RSS, HEADLESS
- `url_patterns`: Approved URL patterns for collection

### RawObservation (`backend/models/raw_observation.py`)
Collection buffer before processing:
- Content hash for deduplication
- Processing state tracking
- Media references
- Extracted locations and timestamps

### Incident (Event Extensions) (`backend/models/event.py`)
Enhanced events with verification workflow:
- `status`: UNVERIFIED → DEVELOPING → CORROBORATED → CONFIRMED (or DEBUNKED)
- `severity`: LOW, MEDIUM, HIGH, CRITICAL
- `occurred_at`: When the incident actually happened
- `region_id`: Link to geographic region
- Admin override with audit trail

### Region (`backend/models/region.py`)
Geographic area state tracking:
- Hierarchical (Global → Continent → Country → Admin1/2 → City)
- Status: GREEN, YELLOW, RED
- Multi-dimensional scores:
  - Physical state (0-100)
  - Migration pressure (0-100)
  - Security stability (0-100)
  - Socioeconomic stress (0-100)
  - Information reliability (0-100)

### Indicator (`backend/models/indicator.py`)
Slow-moving regional trends:
- Domain: GEOPOLITICAL, MIGRATION, SECURITY, ECONOMIC, INFRASTRUCTURE, HEALTH
- Current value with 24h and 7d deltas
- Historical values for trend detection

### Report (`backend/models/report.py`)
Leadership-ready outputs:
- Daily SITREP
- Weekly Brief
- Executive summary, key developments, areas to watch
- Confidence notes and provenance

## Collection Layer (`backend/collectors/`)

Pluggable collector architecture:

| Collector | Sources | Trust Level |
|-----------|---------|-------------|
| `OfficialCollector` | Government advisories, GDACS, ReliefWeb | High (80+) |
| `NewsCollector` | Reuters, BBC, AP news feeds | Medium-High (65-75) |
| `RSSCollector` | General RSS/Atom feeds | Varies |

All collectors output `RawObservation` objects with automatic deduplication via content hash.

### Orchestrator
`CollectorOrchestrator` coordinates collection:
- Routes sources to appropriate collectors
- Handles persistence with deduplication
- Tracks collection statistics

## Processing Pipeline

### Normalization (`backend/services/normalization_service.py`)
RawObservation → Incident:
1. Extract locations with geo-confidence
2. Extract/normalize timestamps
3. Auto-classify category and severity
4. Tag domains (migration, political, security, etc.)
5. Calculate initial confidence

### Verification (`backend/services/verification_service.py`)
Confidence scoring with:
- Source `trust_baseline` integration
- Corroboration boost (diminishing returns per source)
- Visual evidence boost (+15%)
- Official confirmation boost (+20%)
- Penalties for recycled media, geo/time inconsistency

Confidence → Status mapping (thresholds set high - lives depend on accuracy):
| Confidence | Status | Meaning |
|------------|--------|-------|
| < 40% | UNVERIFIED | Unsubstantiated claim |
| 40-74% | DEVELOPING | Being verified, not yet reliable |
| 75%+ | CORROBORATED | Strong multi-source evidence |
| N/A | CONFIRMED | **Admin verification only** |

> **Important:** CONFIRMED status is never set algorithmically. It requires explicit admin verification. CORROBORATED requires 75%+ confidence from multiple independent sources.

## Report Generation (`backend/services/report_service.py`)

### Daily SITREP
- Executive summary (auto-generated)
- Top 10 incidents by severity/confidence
- Region status changes
- Areas to watch
- Confidence notes

### Weekly Brief
- Week-in-review summary
- Major incidents
- Trend analysis
- 7-14 day forward outlook

## API Endpoints

### Incidents (`/incidents`)
- `GET /incidents` - List with filtering (status, severity, category, region)
- `GET /incidents/verification-queue` - Pending verification
- `POST /incidents/{id}/confirm` - Admin confirm
- `POST /incidents/{id}/debunk` - Mark debunked
- `POST /incidents/{id}/override` - Admin status override

### Reports (`/reports`)
- `GET /reports` - List reports
- `POST /reports/daily-sitrep` - Generate Daily SITREP
- `POST /reports/weekly-brief` - Generate Weekly Brief
- `POST /reports/{id}/publish` - Publish report

## Seed Data

Run seed data to populate with sample LATAM regions and indicators:

```bash
cd backend
python -m seed_data
```

Creates:
- Regions: Global, LATAM, Venezuela (RED), Colombia (YELLOW), Europe
- Sources: GDACS, ReliefWeb, UNHCR, Reuters, BBC
- Indicators: Venezuela Migration Pressure (90/100), Colombia Inflow Index
- Sample incidents with various verification states

## Database Migration

Apply new schema:

```bash
alembic upgrade head
```

Migration `006_world_awareness_models` adds:
- New tables: regions, raw_observations, incident_evidence, indicators, reports
- Extended: sources (trust_baseline, collection_method), events (status, severity, admin override)
