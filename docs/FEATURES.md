# Good Shepherd Features Guide

## Overview

Good Shepherd is a comprehensive security intelligence platform designed to keep missionaries and aid workers safe in challenging environments. This guide covers all major features.

---

## 1. Real-Time Updates (WebSocket)

### Description
Receive instant notifications about security events, alerts, and geofence triggers without polling.

### How It Works
- Connect to the WebSocket endpoint at `/ws`
- Subscribe to specific regions, categories, or threat levels
- Receive push notifications for matching events

### Usage Example (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Subscribe to high-threat events in Europe
  ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
      regions: ['europe'],
      threat_levels: ['high', 'critical']
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'event:new') {
    console.log('New event:', message.data);
  }
};
```

---

## 2. Offline-First PWA

### Description
Continue working even without internet connectivity. All critical data is cached locally.

### Features
- **IndexedDB Caching**: Events, alerts, and user data stored locally
- **Background Sync**: Queued actions sync when connectivity returns
- **Service Worker**: Caches static assets and API responses
- **Map Tiles**: Offline map access for previously viewed areas

### How It Works
1. Data is fetched with network-first strategy
2. Successful responses are cached in IndexedDB
3. When offline, cached data is served
4. User actions (check-ins, reports) are queued
5. Queued actions sync automatically when online

### Configuration
```javascript
// In your React app
import { useOfflineFirst } from './hooks/useOfflineFirst';

function MyComponent() {
  const { isOnline, pendingActions, fetchWithCache } = useOfflineFirst();
  
  // Fetch with automatic caching
  const events = await fetchWithCache('/api/events', 'events');
}
```

---

## 3. Mobile Missionary Dashboard

### Description
A mobile-optimized interface for field workers to stay informed and check in.

### Features
- **Real-time event feed**: Latest security events
- **Alert notifications**: Critical alerts prominently displayed
- **One-tap check-in**: Quick location reporting
- **Threat level indicator**: Current safety status
- **Collapsible map**: View events geographically
- **Offline support**: Works without connectivity

### Check-In Process
1. Tap "Check In" button
2. App requests location permission
3. Location sent to server
4. Geofence alerts triggered if in danger zone
5. Confirmation displayed

---

## 4. SMS/WhatsApp Alerts (Twilio)

### Description
Receive critical alerts via SMS or WhatsApp when email/app isn't accessible.

### Configuration
Set these environment variables:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890
```

### Recipient Setup
Recipients can be configured with:
- Phone number
- Preferred channel (SMS or WhatsApp)
- Region filters
- Minimum threat level

### Message Format
```
🚨 CRITICAL ALERT: Armed Conflict in Region X
Region: Europe
Priority: Critical
More info: https://example.com/event/123
```

---

## 5. Intelligence Sources

### GDACS (Global Disaster Alert and Coordination System)
- **Data**: Natural disasters (earthquakes, floods, cyclones)
- **Update frequency**: Real-time RSS feed
- **Coverage**: Global

### ACLED (Armed Conflict Location & Event Data)
- **Data**: Political violence, protests, conflict events
- **Update frequency**: Daily
- **Coverage**: Global
- **Requires**: API key (free for humanitarian use)

### US State Department Travel Advisories
- **Data**: Country-level travel warnings
- **Levels**: 1 (Exercise Normal Precautions) to 4 (Do Not Travel)
- **Update frequency**: As issued

### Configuration
```bash
# ACLED (required for conflict data)
ACLED_API_KEY=your_api_key
ACLED_EMAIL=your_email

# GDACS and State Dept work without configuration
```

---

## 6. Geofencing & Location Tracking

### Description
Define danger zones and receive alerts when users enter or exit them.

### Geofence Types

**Circle Geofence**
- Center point (lat/lng)
- Radius in kilometers
- Best for: Point-based threats

**Polygon Geofence**
- List of vertices
- Arbitrary shape
- Best for: Complex boundaries

### Threat Levels
| Level | Description | Color |
|-------|-------------|-------|
| `safe` | No known threats | Green |
| `caution` | Exercise caution | Yellow |
| `warning` | Elevated risk | Orange |
| `danger` | High risk | Red |
| `no_go` | Do not enter | Black |

### Creating Geofences

**From API:**
```bash
curl -X POST http://localhost:8000/api/geofences/circle \
  -H "X-Admin-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conflict Zone",
    "center": {"latitude": 40.0, "longitude": -74.0},
    "radius_km": 15,
    "threat_level": "danger"
  }'
```

**From Event:**
```bash
curl -X POST "http://localhost:8000/api/geofences/from-event?event_id=123&radius_km=10" \
  -H "X-Admin-API-Key: your-key"
```

### Location Updates
```bash
curl -X POST http://localhost:8000/api/location/update \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "latitude": 40.0,
    "longitude": -74.0,
    "accuracy_meters": 10
  }'
```

---

## 7. PDF Reports & Email Digests

### PDF Reports
Generate downloadable situational reports.

**Features:**
- Executive summary
- Event statistics by region/threat level
- Detailed event listings
- Timestamp and generation info

**Generate Report:**
```bash
curl -X POST http://localhost:8000/api/reports/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly Situational Report",
    "region": "Europe",
    "max_events": 100
  }' \
  --output report.pdf
```

### Email Digests
Automated email summaries of security events.

**Subscription Options:**
- Frequency: Daily or Weekly
- Region filters
- Category filters
- Minimum threat level
- Include PDF attachment

**Subscribe:**
```bash
curl -X POST http://localhost:8000/api/digests/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "frequency": "daily",
    "regions": ["europe", "africa"],
    "min_threat_level": "high",
    "include_pdf": true
  }'
```

**Configuration:**
```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_ADDRESS=alerts@example.com
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Dashboard   │  │ Offline Hook │  │ Service Worker    │  │
│  │ Component   │  │ (IndexedDB)  │  │ (Cache/Sync)      │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ WebSocket   │  │ Geofencing   │  │ Alert Engine      │  │
│  │ Manager     │  │ Service      │  │                   │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ PDF Export  │  │ Email Digest │  │ SMS/WhatsApp      │  │
│  │             │  │ Service      │  │ (Twilio)          │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Intelligence Sources                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ GDACS       │  │ ACLED        │  │ State Dept        │  │
│  │ (Disasters) │  │ (Conflicts)  │  │ (Advisories)      │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### For Administrators
1. Set up geofences proactively based on intelligence
2. Configure alert rules for your regions of interest
3. Review and update geofences as situations evolve
4. Monitor WebSocket stats for connectivity issues

### For Field Workers
1. Enable location services on your device
2. Check in regularly, especially when moving
3. Pay attention to threat level indicators
4. Download offline maps for your area
5. Keep the app open for real-time alerts

### For IT Teams
1. Use HTTPS in production
2. Rotate API keys regularly
3. Monitor error logs for failed deliveries
4. Set up redundant notification channels
5. Test offline functionality regularly
