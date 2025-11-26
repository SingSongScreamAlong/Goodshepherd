# Audit Logging & Governance

**The Good Shepherd** includes comprehensive audit logging for organizational accountability, compliance, and security monitoring.

## Overview

The audit logging system tracks all significant user actions within the platform, providing:
- **Accountability**: Know who performed what action and when
- **Compliance**: Meet regulatory requirements for activity tracking
- **Security**: Detect suspicious patterns and unauthorized access attempts
- **Forensics**: Investigate incidents with detailed action history

## What Gets Logged

### Tracked Actions

All audit logs include the following action types:

| Action Type | Description | Examples |
|------------|-------------|----------|
| `create` | Creating new resources | New dossier, watchlist, user |
| `update` | Modifying existing resources | Edit dossier details, update settings |
| `delete` | Removing resources | Delete watchlist, remove dossier |
| `view` | Accessing sensitive information | View event details, export data |
| `export` | Exporting data from platform | CSV export, report generation |
| `login` | User authentication | Successful login attempts |
| `logout` | User session termination | Manual logout |
| `access_denied` | Authorization failures | Attempted unauthorized access |

### Tracked Object Types

Audit logs record actions on these object types:

- **dossier** - Tracked entities (locations, organizations, groups, topics, persons)
- **watchlist** - Collections of dossiers
- **event** - Intelligence events (aggregate-level access tracking)
- **settings** - Organization configuration changes
- **user** - User management actions
- **feedback** - Event feedback submissions

### Audit Log Fields

Each audit log entry contains:

```typescript
{
  id: string;              // Unique audit entry ID
  user_id: string;         // User who performed the action
  user_email: string;      // Email for easy identification
  organization_id: string; // Organization context
  action_type: string;     // Type of action (create, update, delete, etc.)
  object_type: string;     // Type of object affected
  object_id: string;       // ID of the specific object (if applicable)
  description: string;     // Human-readable description
  metadata: object;        // Additional action-specific data
  ip_address: string;      // Client IP address for forensics
  timestamp: DateTime;     // When the action occurred (UTC)
}
```

## API Endpoints

### Get Audit Logs

```http
GET /audit/logs
```

**Query Parameters:**
- `action_type` (optional) - Filter by action type (create, update, delete, etc.)
- `object_type` (optional) - Filter by object type (dossier, watchlist, event, etc.)
- `user_id` (optional) - Filter by specific user
- `days` (default: 30, max: 365) - Number of days to look back
- `page` (default: 1) - Page number for pagination
- `page_size` (default: 50, max: 500) - Items per page

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_email": "analyst@example.org",
    "organization_id": "org-uuid",
    "action_type": "create",
    "object_type": "dossier",
    "object_id": "dossier-uuid",
    "description": "Created new location dossier for Paris",
    "metadata": {
      "dossier_type": "location",
      "name": "Paris"
    },
    "ip_address": "203.0.113.42",
    "timestamp": "2025-11-26T14:30:00Z"
  }
]
```

### Get Audit Statistics

```http
GET /audit/stats?days=30
```

**Response:**
```json
{
  "total_actions": 1247,
  "actions_by_type": {
    "create": 345,
    "update": 567,
    "delete": 89,
    "view": 234,
    "export": 12
  },
  "objects_by_type": {
    "dossier": 456,
    "watchlist": 123,
    "event": 234,
    "settings": 45
  },
  "most_active_users": [
    {
      "user_email": "analyst1@example.org",
      "action_count": 456
    },
    {
      "user_email": "admin@example.org",
      "action_count": 234
    }
  ]
}
```

## Frontend Integration

### Accessing the Audit Log

1. Navigate to **Admin → Audit Log** in the main navigation
2. Use filters to narrow down results:
   - **Action Type**: Filter by specific actions
   - **Object Type**: Filter by resource type
   - **Time Period**: Choose 7, 30, 90, or 365 days
3. Click "View" on any entry to see detailed information

### Admin Requirements

- Only users with **Admin** role can view audit logs
- Audit logs are organization-scoped (can only view logs for your organization)
- All viewing of audit logs is itself logged (meta-auditing)

## Use Cases

### 1. Compliance Reporting

Generate audit reports for regulatory compliance:

```bash
# Get all actions in last 90 days
GET /audit/logs?days=90&page_size=500

# Export to CSV for compliance documentation
```

### 2. Security Incident Investigation

Investigate suspicious activity:

```bash
# Find all delete actions by specific user
GET /audit/logs?action_type=delete&user_id={user_uuid}

# Check for access_denied events (failed authorization)
GET /audit/logs?action_type=access_denied&days=7
```

### 3. User Activity Monitoring

Monitor user behavior patterns:

```bash
# Get statistics for last 30 days
GET /audit/stats?days=30

# Review most active users
# Identify unusual activity patterns
```

### 4. Data Change Tracking

Track modifications to critical resources:

```bash
# Find all updates to organization settings
GET /audit/logs?action_type=update&object_type=settings

# Review all dossier deletions
GET /audit/logs?action_type=delete&object_type=dossier
```

## Data Retention

### Retention Policies

- **Default Retention**: 365 days (configurable via organization settings)
- **Minimum Retention**: 30 days (for compliance)
- **Auto-Cleanup**: Automated job purges logs older than retention period

### Compliance Considerations

- **GDPR**: Audit logs may contain user identification data
- **Data Subject Rights**: Users can request their audit log history
- **Right to Erasure**: When user is deleted, audit logs are anonymized (user_id set to NULL, but actions remain)

## Security Considerations

### Tamper-Resistance

- Audit logs are **append-only** (cannot be modified or deleted by users)
- All timestamps are UTC for consistency
- IP addresses logged for forensic analysis

### Access Control

- Only organization **Admins** can view audit logs
- Logs are strictly organization-scoped (multi-tenant isolation)
- Viewing audit logs generates its own audit entry

### Privacy Safeguards

- No sensitive data (passwords, tokens) in audit metadata
- Personal data minimization (only essential fields logged)
- IP addresses can be anonymized if required by regulations

## Best Practices

### For Administrators

1. **Review Regularly**: Check audit logs weekly for unusual patterns
2. **Set Alerts**: Monitor for specific action types (deletes, exports)
3. **Export Archives**: Periodically export logs for long-term storage
4. **Investigate Anomalies**: Follow up on suspicious activity immediately

### For Developers

1. **Log Meaningful Actions**: Focus on security-relevant operations
2. **Include Context**: Use metadata field for action-specific details
3. **Don't Over-Log**: Avoid logging every single view/read operation
4. **Test Logging**: Verify audit entries are created correctly

## Integration Examples

### Backend: Logging an Action

```python
from backend.core.audit import log_audit_action, AuditAction, AuditObjectType

# After creating a dossier
log_audit_action(
    db=db,
    user=current_user,
    organization_id=org_id,
    action_type=AuditAction.CREATE,
    object_type=AuditObjectType.DOSSIER,
    object_id=dossier.id,
    description=f"Created {dossier.dossier_type} dossier: {dossier.name}",
    metadata={"dossier_type": dossier.dossier_type},
    request=request,  # Extracts IP and user agent
)
```

### Frontend: Viewing Audit Logs

```typescript
// Fetch audit logs with filters
const response = await apiClient.get('/audit/logs', {
  params: {
    action_type: 'delete',
    days: 30,
    page: 1,
    page_size: 50,
  },
});

const auditLogs = response.data;
```

## Troubleshooting

### Logs Not Appearing

1. **Check permissions**: Ensure you have Admin role
2. **Verify filters**: Clear all filters and try again
3. **Check time range**: Expand date range (actions may be older)

### Missing Details

1. **Metadata empty**: Some actions don't include additional metadata
2. **User email null**: "System" actions (automated processes)
3. **IP address null**: Backend/worker actions (no HTTP request context)

## Related Documentation

- [Data Model & Multi-Tenancy](DATA_MODEL.md) - Organization-scoped data architecture
- [Risk Mitigation & Ethics](RISK_MITIGATION.md) - Ethical use of audit data
- [Organization Settings](ORG_SETTINGS.md) - Configure audit retention policies

---

**Version**: 0.8.0
**Last Updated**: 2025-11-26
