# Organization Settings

**The Good Shepherd** provides comprehensive organization-level settings that allow administrators to customize platform behavior, default filters, alert thresholds, and display preferences without requiring code deployment.

## Overview

Organization settings enable:
- **Customization**: Tailor the platform to your organization's needs
- **Default Preferences**: Set organization-wide defaults for all users
- **Regional Focus**: Prioritize or exclude specific geographic regions
- **Alert Configuration**: Define what triggers high-priority alerts
- **Feature Toggles**: Enable/disable specific platform capabilities
- **Data Retention**: Control how long data is stored

## Settings Categories

### 1. Default Filters

Configure default filter preferences applied to stream and map views.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `default_categories` | Array | Event categories shown by default | All categories |
| `default_sentiment_filter` | String | Sentiment filter (positive/neutral/negative/null) | null (all) |
| `default_min_relevance` | Float | Minimum relevance threshold (0.0-1.0) | 0.5 |

**Example Configuration:**
```json
{
  "default_categories": ["protest", "crime", "religious_freedom", "political"],
  "default_sentiment_filter": null,
  "default_min_relevance": 0.7
}
```

**Use Case:**
*Your organization focuses on security-related events. Set default categories to only show crime, protest, and infrastructure events, with minimum relevance of 0.7 to filter noise.*

### 2. Alert Thresholds

Define what events trigger high-priority alerts for your organization.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `high_priority_threshold` | Float | Relevance score required for high-priority (0.0-1.0) | 0.8 |
| `alert_categories` | Array | Which categories trigger alerts | null (all) |
| `alert_sentiment_types` | Array | Which sentiments trigger alerts | null (all) |

**Example Configuration:**
```json
{
  "high_priority_threshold": 0.85,
  "alert_categories": ["crime", "protest", "health"],
  "alert_sentiment_types": ["negative"]
}
```

**Use Case:**
*Only alert on high-relevance (>0.85) negative events in crime, protest, and health categories to focus on safety-critical incidents.*

### 3. Feature Toggles

Enable or disable specific platform features for your organization.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `enable_email_alerts` | Boolean | Send email notifications for high-priority events | false |
| `enable_clustering` | Boolean | Automatically group similar events | true |
| `enable_feedback_collection` | Boolean | Allow users to provide event feedback | true |
| `enable_audit_logging` | Boolean | Track all user actions for accountability | true |

**Example Configuration:**
```json
{
  "enable_email_alerts": true,
  "enable_clustering": true,
  "enable_feedback_collection": true,
  "enable_audit_logging": true
}
```

**Use Case:**
*Enable email alerts for real-time notifications, keep clustering and feedback enabled for better intelligence, and maintain audit logging for compliance.*

### 4. Display Preferences

Customize how information is displayed in the interface.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `default_map_zoom` | Integer | Initial map zoom level (1-18) | 5 |
| `default_map_center_lat` | Float | Map center latitude | null |
| `default_map_center_lon` | Float | Map center longitude | null |
| `events_per_page` | Integer | Number of events shown per page | 20 |

**Example Configuration:**
```json
{
  "default_map_zoom": 6,
  "default_map_center_lat": 48.8566,
  "default_map_center_lon": 2.3522,
  "events_per_page": 50
}
```

**Use Case:**
*Center map on Paris with zoom level 6 to focus on France and surrounding countries. Show 50 events per page for power users.*

### 5. Data Retention

Control how long data is stored in the system.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `event_retention_days` | Integer | Days to keep events (null = forever) | null |
| `audit_log_retention_days` | Integer | Days to keep audit logs (minimum 30) | 365 |

**Example Configuration:**
```json
{
  "event_retention_days": 180,
  "audit_log_retention_days": 730
}
```

**Use Case:**
*Keep events for 6 months (sufficient for analysis) and audit logs for 2 years (compliance requirement).*

**Important Notes:**
- Events older than retention period are automatically deleted
- Audit logs have 30-day minimum for compliance
- Setting `event_retention_days` to `null` keeps events indefinitely

### 6. Regional Focus

Prioritize or exclude specific geographic regions.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `focus_regions` | Array | Regions to prioritize | null (all) |
| `exclude_regions` | Array | Regions to filter out completely | null (none) |

**Available Regions:**
- Western Europe
- Eastern Europe
- Northern Europe
- Southern Europe
- Central Europe
- Balkans

**Example Configuration:**
```json
{
  "focus_regions": ["Western Europe", "Central Europe"],
  "exclude_regions": []
}
```

**Use Case:**
*Your mission operates primarily in Western and Central Europe. Prioritize events from these regions while still seeing others.*

**Regional Filtering Behavior:**
- **focus_regions**: Events from these regions score higher in relevance
- **exclude_regions**: Events from these regions are completely filtered out
- Empty arrays mean no filtering (all regions treated equally)

### 7. Custom Configuration

Flexible JSON field for organization-specific settings.

**Available Settings:**

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `custom_config` | JSON | Arbitrary key-value pairs for custom settings | null |

**Example Configuration:**
```json
{
  "custom_config": {
    "theme": "dark",
    "language": "fr",
    "integrations": {
      "slack_webhook": "https://hooks.slack.com/..."
    }
  }
}
```

**Use Case:**
*Store custom application preferences that don't fit into standard settings categories.*

## API Endpoints

### Get Organization Settings

```http
GET /settings
```

**Response:**
```json
{
  "id": "settings-uuid",
  "organization_id": "org-uuid",
  "default_categories": ["protest", "crime", "political"],
  "default_sentiment_filter": null,
  "default_min_relevance": 0.7,
  "high_priority_threshold": 0.85,
  "alert_categories": ["crime", "protest"],
  "alert_sentiment_types": ["negative"],
  "enable_email_alerts": true,
  "enable_clustering": true,
  "enable_feedback_collection": true,
  "enable_audit_logging": true,
  "default_map_zoom": 6,
  "default_map_center_lat": 48.8566,
  "default_map_center_lon": 2.3522,
  "events_per_page": 50,
  "event_retention_days": 180,
  "audit_log_retention_days": 730,
  "focus_regions": ["Western Europe", "Central Europe"],
  "exclude_regions": [],
  "custom_config": null
}
```

**Behavior:**
- If no settings exist, default settings are automatically created
- Returns current settings for authenticated user's organization

### Update Organization Settings

```http
PUT /settings
```

**Request Body (Partial Update):**
```json
{
  "default_min_relevance": 0.8,
  "enable_email_alerts": true,
  "events_per_page": 100
}
```

**Response:**
```json
{
  "id": "settings-uuid",
  "organization_id": "org-uuid",
  // ... all settings with updates applied
}
```

**Behavior:**
- Only provided fields are updated (partial update)
- Null values explicitly set fields to null
- Omitted fields remain unchanged
- Change is audited (logged to audit_logs table)

### Reset to Defaults

```http
POST /settings/reset
```

**Behavior:**
- Deletes current custom settings
- Next GET request will auto-create new default settings
- Change is audited

## Frontend Integration

### Accessing Settings

1. Navigate to **Admin → Settings** in the main navigation
2. Admin-only page with tabbed sections:
   - Default Filters
   - Alert Thresholds
   - Feature Toggles
   - Display Preferences
   - Data Retention
   - Regional Focus

### Settings UI

**Interactive Controls:**
- **Checkboxes**: Multi-select for categories and regions
- **Dropdowns**: Single-select for sentiment filter
- **Sliders**: Range inputs for thresholds and relevance
- **Number Inputs**: Precise values for zoom, pagination, retention
- **Toggle Switches**: Feature enable/disable

**Actions:**
- **Save Settings**: Apply changes (triggers audit log)
- **Reset to Defaults**: Restore default configuration

### Settings Effects

Changes take effect:
- **Immediately**: Feature toggles, display preferences
- **Next Load**: Default filters (applied on page refresh)
- **Background**: Data retention (scheduled cleanup job)

## Integration with Platform

### Stream View

Default filters automatically applied:
```typescript
// User opens stream view
const settings = await fetchOrganizationSettings();

// Apply default filters
const defaultFilters = {
  categories: settings.default_categories || [],
  sentiment: settings.default_sentiment_filter || null,
  minRelevance: settings.default_min_relevance || 0.5,
};

// User can override defaults for their session
```

### Map View

Map centered on organization's focus region:
```typescript
const settings = await fetchOrganizationSettings();

const mapConfig = {
  zoom: settings.default_map_zoom || 5,
  center: settings.default_map_center_lat && settings.default_map_center_lon
    ? [settings.default_map_center_lat, settings.default_map_center_lon]
    : [50.0, 10.0], // Default to Europe
};
```

### Alerts

High-priority events determined by settings:
```typescript
function isHighPriority(event, settings) {
  // Check relevance threshold
  if (event.relevance_score < settings.high_priority_threshold) {
    return false;
  }

  // Check category filter
  if (settings.alert_categories && settings.alert_categories.length > 0) {
    if (!settings.alert_categories.includes(event.category)) {
      return false;
    }
  }

  // Check sentiment filter
  if (settings.alert_sentiment_types && settings.alert_sentiment_types.length > 0) {
    if (!settings.alert_sentiment_types.includes(event.sentiment)) {
      return false;
    }
  }

  return true;
}
```

## Best Practices

### For Administrators

1. **Start with Defaults**: Use default settings initially, adjust based on usage
2. **Consult Team**: Gather input from analysts before changing filters
3. **Test Changes**: Verify settings changes have desired effect
4. **Document Rationale**: Note why specific settings were chosen
5. **Review Regularly**: Reassess settings quarterly

### Configuration Examples

#### Security-Focused Organization
```json
{
  "default_categories": ["crime", "protest", "infrastructure", "political"],
  "default_min_relevance": 0.8,
  "high_priority_threshold": 0.9,
  "alert_categories": ["crime", "protest"],
  "enable_email_alerts": true,
  "focus_regions": ["Western Europe"]
}
```

#### Humanitarian Mission
```json
{
  "default_categories": ["health", "migration", "community_event", "infrastructure"],
  "default_min_relevance": 0.6,
  "high_priority_threshold": 0.75,
  "alert_categories": ["health", "migration"],
  "enable_email_alerts": true,
  "focus_regions": ["Southern Europe", "Balkans"]
}
```

#### Research Organization
```json
{
  "default_categories": [],  // All categories
  "default_min_relevance": 0.5,
  "high_priority_threshold": 0.7,
  "alert_categories": [],  // All categories
  "enable_email_alerts": false,
  "event_retention_days": null,  // Keep everything
  "events_per_page": 100
}
```

## Troubleshooting

### Settings Not Taking Effect

1. **Refresh page**: Some settings require page reload
2. **Check permissions**: Ensure you have Admin role
3. **Verify save**: Check for success message after saving
4. **Clear cache**: Browser cache may show old settings

### Can't Update Settings

1. **Admin role required**: Only admins can modify settings
2. **Network issues**: Check internet connection
3. **Validation errors**: Ensure values are within valid ranges

### Unexpected Filtering

1. **Check default_categories**: May be filtering out desired categories
2. **Review min_relevance**: Too high may hide relevant events
3. **Verify exclude_regions**: Events from excluded regions won't appear

## Migration & Compatibility

### Upgrading from Previous Versions

- Settings automatically migrate to new schema
- Missing fields populated with defaults
- No data loss during migration

### Backward Compatibility

- Frontend gracefully handles missing settings
- Defaults used if settings endpoint unavailable
- Progressive enhancement approach

## Security & Privacy

### Access Control

- Only **Admin** role can view/modify settings
- Settings are **organization-scoped** (multi-tenant)
- Changes logged to audit trail

### Data Sensitivity

- No sensitive data in settings (no passwords, API keys)
- Regional preferences for mission planning (not PII)
- Custom config should not contain secrets (use environment variables)

## Related Documentation

- [Data Model & Multi-Tenancy](DATA_MODEL.md) - Organization-scoped architecture
- [Audit Logging](AUDIT_LOGGING.md) - Settings changes are audited
- [Feedback System](FEEDBACK_SYSTEM.md) - Feedback can be toggled via settings

---

**Version**: 0.8.0
**Last Updated**: 2025-11-26
