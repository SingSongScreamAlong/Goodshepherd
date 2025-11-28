# Good Shepherd API Documentation

## Overview

Good Shepherd API v0.3.0 provides real-time security intelligence for missionary safety. This document covers all available endpoints.

**Base URL:** `http://localhost:8000`

## Authentication

Some endpoints require admin authentication via the `X-Admin-API-Key` header.

```bash
curl -H "X-Admin-API-Key: your-api-key" http://localhost:8000/api/endpoint
```

---

## System Endpoints

### Health Check

```
GET /api/health
```

Returns the API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Events

### List Recent Events

```
GET /api/events
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum events to return |
| `offset` | integer | 0 | Pagination offset |

### Search Events

```
GET /api/events/search
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query |
| `region` | string | Filter by region |
| `category` | string | Filter by category |
| `threat_level` | string | Filter by threat level |
| `limit` | integer | Maximum results |

### Get Event by ID

```
GET /api/events/{event_id}
```

---

## Geofencing

### List Geofences

```
GET /api/geofences
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | true | Only return non-expired geofences |

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Danger Zone",
    "geofence_type": "circle",
    "threat_level": "danger",
    "description": "Armed conflict area",
    "created_at": "2025-01-15T10:00:00Z",
    "expires_at": null
  }
]
```

### Get Geofence

```
GET /api/geofences/{geofence_id}
```

### Create Circle Geofence

```
POST /api/geofences/circle
```

**Requires:** Admin API Key

**Request Body:**
```json
{
  "name": "Danger Zone",
  "center": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "radius_km": 10.0,
  "threat_level": "danger",
  "description": "Armed conflict area",
  "expires_at": "2025-02-15T00:00:00Z"
}
```

**Threat Levels:** `safe`, `caution`, `warning`, `danger`, `no_go`

### Create Polygon Geofence

```
POST /api/geofences/polygon
```

**Requires:** Admin API Key

**Request Body:**
```json
{
  "name": "Restricted Area",
  "vertices": [
    {"latitude": 40.0, "longitude": -74.0},
    {"latitude": 40.0, "longitude": -73.0},
    {"latitude": 41.0, "longitude": -73.0},
    {"latitude": 41.0, "longitude": -74.0}
  ],
  "threat_level": "warning"
}
```

### Create Geofence from Event

```
POST /api/geofences/from-event?event_id={id}&radius_km=10
```

**Requires:** Admin API Key

Creates a circular geofence centered on an event's location.

### Delete Geofence

```
DELETE /api/geofences/{geofence_id}
```

**Requires:** Admin API Key

---

## Location Tracking

### Update User Location

```
POST /api/location/update
```

**Request Body:**
```json
{
  "user_id": "user-123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "accuracy_meters": 10.0
}
```

**Response:**
```json
{
  "user_id": "user-123",
  "current_threat_level": "danger",
  "alerts": [
    {
      "id": "uuid",
      "user_id": "user-123",
      "geofence_id": "uuid",
      "geofence_name": "Danger Zone",
      "event_type": "enter",
      "threat_level": "danger",
      "timestamp": "2025-01-15T10:30:00Z",
      "message": "Entered danger zone: Danger Zone"
    }
  ],
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Get User Threat Level

```
GET /api/location/{user_id}/threat-level
```

**Response:**
```json
{
  "user_id": "user-123",
  "threat_level": "danger",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Get Nearby Threats

```
GET /api/location/nearby-threats?latitude=40.7&longitude=-74.0&radius_km=50
```

**Response:**
```json
[
  {
    "geofence_id": "uuid",
    "name": "Danger Zone",
    "threat_level": "danger",
    "distance_km": 5.2,
    "description": "Armed conflict area"
  }
]
```

---

## Reports

### Generate PDF Report

```
POST /api/reports/pdf
```

**Request Body:**
```json
{
  "title": "Daily Situational Report",
  "region": "Europe",
  "max_events": 100
}
```

**Response:** PDF file download

### Download Report as PDF

```
GET /api/reports/{report_id}/pdf
```

**Response:** PDF file download

---

## Email Digests

### List Subscriptions

```
GET /api/digests/subscriptions
```

**Requires:** Admin API Key

### Create Subscription

```
POST /api/digests/subscriptions
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "frequency": "daily",
  "regions": ["europe", "asia"],
  "min_threat_level": "high",
  "include_pdf": true
}
```

**Frequencies:** `daily`, `weekly`

### Get Subscription

```
GET /api/digests/subscriptions/{email}
```

### Delete Subscription

```
DELETE /api/digests/subscriptions/{email}
```

### Send Test Digest

```
POST /api/digests/send-test?email={email}
```

**Requires:** Admin API Key

---

## WebSocket

### Connect

```
ws://localhost:8000/ws
```

### Client Messages

**Subscribe to events:**
```json
{
  "type": "subscribe",
  "data": {
    "regions": ["europe", "asia"],
    "categories": ["conflict"],
    "threat_levels": ["high", "critical"]
  }
}
```

**Unsubscribe:**
```json
{
  "type": "unsubscribe"
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

### Server Messages

**New Event:**
```json
{
  "type": "event:new",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "id": "uuid",
    "title": "Event Title",
    "region": "Europe",
    "threat_level": "high"
  }
}
```

**Alert Triggered:**
```json
{
  "type": "alert:triggered",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "alert_id": "uuid",
    "title": "Critical Alert",
    "priority": "critical"
  }
}
```

**Geofence Alert:**
```json
{
  "type": "alert:triggered",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "type": "geofence_alert",
    "user_id": "user-123",
    "geofence_name": "Danger Zone",
    "event_type": "enter",
    "threat_level": "danger"
  }
}
```

**Heartbeat:**
```json
{
  "type": "heartbeat",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### WebSocket Stats

```
GET /api/ws/stats
```

**Response:**
```json
{
  "connected_clients": 5,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Alert Rules

### List Alert Rules

```
GET /api/alerts/rules
```

### Create Alert Rule

```
POST /api/alerts/rules
```

**Requires:** Admin API Key

**Request Body:**
```json
{
  "name": "High Threat Europe",
  "description": "Alert for high threat events in Europe",
  "regions": ["europe"],
  "categories": ["conflict", "attack"],
  "minimum_threat": "high",
  "minimum_credibility": 0.7,
  "lookback_minutes": 60,
  "priority": "critical"
}
```

### Update Alert Rule

```
PUT /api/alerts/rules/{rule_id}
```

**Requires:** Admin API Key

### Delete Alert Rule

```
DELETE /api/alerts/rules/{rule_id}
```

**Requires:** Admin API Key

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized (missing or invalid API key)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable
