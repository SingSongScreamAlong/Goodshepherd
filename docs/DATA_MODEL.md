# Data Model & Multi-Tenancy

## Overview

The Good Shepherd uses a hybrid multi-tenant model that balances shared intelligence (events are global) with organization-specific configurations (dossiers and watchlists are private).

## Tenancy Model

### Global (Shared Across Organizations)

**Events** are GLOBAL - they represent real-world occurrences and are visible to all authenticated users.

**Rationale:**
- Events describe public incidents from public sources (OSINT)
- Multiple organizations benefit from seeing the same event stream
- Organizations can filter/prioritize events based on their interests

**Model:**
```python
class Event(Base):
    # No organization_id field
    # All authenticated users can read all events
    event_id: UUID
    timestamp: DateTime
    category: EventCategory
    location: Geography
    sentiment: SentimentEnum
    # ... no organization scoping
```

**Access Control:**
- **Read**: All authenticated users
- **Write**: System only (via ingest workers)
- **Update**: System only (via enrichment and fusion)
- **Delete**: Superuser only

### Organization-Scoped (Private)

**Dossiers** are ORG-SCOPED - each organization maintains its own collection of tracked entities, locations, and topics.

**Model:**
```python
class Dossier(Base):
    id: UUID
    organization_id: UUID  # Foreign key to organizations table
    name: str
    dossier_type: DossierType  # location, organization, group, topic, person
    description: Text
    aliases: JSON  # Alternative names
    tags: JSON  # Org-specific tags
    notes: Text  # Org-specific notes
    # Statistics auto-computed from global events
    event_count: int
    last_event_timestamp: DateTime
```

**Access Control:**
- Users can only see/modify dossiers belonging to their organization
- Queries must filter by `organization_id`
- Creation automatically sets `organization_id` from authenticated user's org

**Watchlists** are ORG-SCOPED and USER-SCOPED.

**Model:**
```python
class Watchlist(Base):
    id: UUID
    organization_id: UUID  # Org boundary
    user_id: UUID  # Personal watchlists
    name: str
    priority: WatchlistPriority
    dossiers: List[Dossier]  # Many-to-many
```

**Access Control:**
- Users can only see watchlists from their organization
- Users can create personal watchlists
- Future: Shared org-wide watchlists (TBD)

## User-Organization Relationship

Users can belong to multiple organizations (many-to-many), with a role in each.

**Model:**
```python
class User(Base):
    id: UUID
    email: str
    organizations: List[Organization]  # Many-to-many

# Association table
user_organization:
    user_id: UUID
    organization_id: UUID
    role: RoleEnum  # admin, analyst, viewer
```

### Current Organization Selection

**Current Implementation:**
- When a user authenticates, the system uses their **first organization** in the list
- Helper dependency: `get_current_organization()` returns `user.organizations[0]`

**Future Enhancement:**
- Allow users to select which organization context they're operating in
- Store selected org_id in JWT token or session
- UI switcher for multi-org users

## Roles & Permissions

### Role Hierarchy

1. **Viewer** (read-only)
   - View events, dossiers, watchlists, dashboard
   - Cannot create/modify/delete

2. **Analyst** (read-write)
   - All viewer permissions
   - Create/edit/delete dossiers and watchlists
   - Annotate events (future)
   - Provide feedback on event relevance

3. **Admin** (full control within org)
   - All analyst permissions
   - Manage organization settings
   - Invite/remove users from organization
   - Configure ingest sources (future)

4. **Superuser** (global)
   - System-level access
   - Can create organizations
   - Can delete events (cleanup)
   - Access to all organizations

### Permission Enforcement

**Backend:**
- All endpoints requiring org-scoping use `Depends(get_current_organization)`
- Queries filter by `organization_id` automatically
- Role checks use `current_user.role` from user_organization table (future)

**Example:**
```python
@router.get("/dossiers", response_model=List[DossierResponse])
def list_dossiers(
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    # Automatically scoped to user's organization
    return db.query(Dossier).filter(Dossier.organization_id == org_id).all()
```

## Data Flow

### Event Ingestion (Global)

```
External Sources (RSS, APIs)
    ↓
Ingest Workers
    ↓
Raw Events (stored globally)
    ↓
LLM Enrichment (async)
    ↓
Enriched Events (global, visible to all)
    ↓
Fusion/Clustering (groups related events)
    ↓
Dashboard, Stream, Map Views
```

### Dossier Matching (Org-Specific)

```
Global Events
    ↓
Dossier Service (per-organization)
    ↓
Match events to org's dossiers (by name, alias, location)
    ↓
Update dossier statistics
    ↓
Org-specific dossier views
```

## Security Boundaries

### What is Shared?
- **Events**: All organizations see the same event stream
- **Categories/Taxonomy**: Shared classification system
- **Enrichment**: LLM analysis results

### What is Private?
- **Dossiers**: Each org's tracked entities
- **Watchlists**: Personal and org-specific
- **Notes/Tags**: Org-specific annotations
- **User Data**: Email, names, roles

### OSINT Compliance

**Global Constraints (applies to ALL data):**
- ❌ No private individuals (only public officials in `person` dossiers)
- ❌ No non-public data sources
- ❌ No intrusion or unauthorized access
- ✅ All data must be publicly available
- ✅ Clear source attribution

## Database Design Principles

1. **Events are immutable** (write-once, system-only updates)
2. **Organization boundaries are enforced at query time**
3. **Statistics are computed, not manually entered**
4. **User context determines data access**
5. **Audit trails for all mutations** (future)

## API Design Patterns

### Standard Dependency Injection

```python
from backend.core.dependencies import get_current_user, get_current_org_id

@router.get("/endpoint")
def endpoint(
    current_user: User = Depends(get_current_user),  # Authentication
    org_id: UUID = Depends(get_current_org_id),      # Organization scoping
    db: Session = Depends(get_db)
):
    # org_id is automatically extracted from current_user's organization
    # All queries should filter by org_id where applicable
    ...
```

### Global Endpoints (Events)

```python
@router.get("/events")
def list_events(
    current_user: User = Depends(get_current_user),  # Auth required
    db: Session = Depends(get_db)
):
    # No org_id filtering - events are global
    return db.query(Event).all()
```

### Org-Scoped Endpoints (Dossiers)

```python
@router.get("/dossiers")
def list_dossiers(
    org_id: UUID = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    # Automatically scoped to user's org
    return db.query(Dossier).filter(Dossier.organization_id == org_id).all()
```

## Future Enhancements

### Planned Improvements

1. **Organization Switcher**
   - UI control for multi-org users to switch context
   - Store selected org in JWT or session

2. **Fine-Grained Permissions**
   - Role-based access control (RBAC) enforcement
   - Permission checks in endpoints (not just org scoping)

3. **Org-Specific Event Overlays**
   - Private notes/annotations on global events
   - Org-specific tags without duplicating events

4. **Shared Watchlists**
   - Org-wide watchlists (not just personal)
   - Team collaboration features

5. **Audit Logging**
   - Track all CRUD operations
   - Who created/modified what, when

6. **Event Subscriptions**
   - Org-specific event filtering rules
   - Only show events matching org's region of interest

## Migration Notes

If moving from single-tenant to stricter multi-tenant:

1. Add org boundary checks to ALL endpoints
2. Create migration to assign orphaned data to orgs
3. Add foreign key constraints for org_id fields
4. Update tests to include org scoping scenarios

---

**Version:** 0.8.0
**Last Updated:** 2025-11-25
