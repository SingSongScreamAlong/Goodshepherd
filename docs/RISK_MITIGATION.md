# Risk Mitigation & Ethical Safeguards

**Document Purpose:** Outline potential misuse scenarios, technical safeguards, and ethical guardrails for The Good Shepherd OSINT platform.

**Last Updated:** 2025-11-25
**Version:** 0.8.0

---

## Table of Contents

1. [Mission and Values](#mission-and-values)
2. [Potential Misuse Scenarios](#potential-misuse-scenarios)
3. [Technical Safeguards](#technical-safeguards)
4. [Organizational Controls](#organizational-controls)
5. [Monitoring and Auditing](#monitoring-and-auditing)
6. [Incident Response](#incident-response)
7. [Legal and Compliance](#legal-and-compliance)

---

## Mission and Values

### Core Purpose
The Good Shepherd exists to provide **situational awareness for missionary safety and operations** in Europe. It is:

- **OSINT-only** - Public data sources exclusively
- **Non-kinetic** - No tactical, operational, or targeting capabilities
- **Defensive** - Focused on awareness and protection, never offense
- **Ethical** - Respects privacy, dignity, and human rights

### What We Are NOT
- ❌ **NOT a targeting system** - No individual tracking or profiling
- ❌ **NOT surveillance** - No private data, no facial recognition, no intrusive monitoring
- ❌ **NOT command & control** - No dispatch, routing, or operational coordination
- ❌ **NOT intelligence gathering on individuals** - Only aggregated open-source events

---

## Potential Misuse Scenarios

### Scenario 1: Individual Tracking
**Risk:** Attempting to track private individuals using platform features.

**Why It's Prohibited:**
- Violates ethical OSINT principles
- Infringes on privacy rights
- Contradicts platform mission (events, not people)

**Technical Prevention:**
- Events are de-identified and aggregated
- No PII collection in data model
- No facial recognition or biometric capabilities
- No location tracking of individuals

**Detection:**
- Audit logs track all queries and data access
- Unusual access patterns trigger alerts
- Manual review of high-volume queries

---

### Scenario 2: Tactical or Kinetic Use
**Risk:** Using platform data for operational planning, targeting, or tactical decision-making.

**Why It's Prohibited:**
- Platform designed for awareness, not action
- No real-time targeting or dispatch capabilities
- Missionary context: defensive posture only

**Technical Prevention:**
- No real-time alerts suitable for tactical response
- Event data intentionally delayed (not real-time)
- No integration with operational systems
- No routing, dispatch, or C2 features

**Organizational Control:**
- Terms of Service explicitly prohibit tactical use
- User training emphasizes awareness-only mission
- Organizations vetted before platform access

---

### Scenario 3: Law Enforcement or Intelligence Gathering
**Risk:** Government agencies using platform for surveillance or intelligence operations.

**Why It's Prohibited:**
- Platform designed for missionary safety, not law enforcement
- Data sources and enrichment optimized for different use case
- Potential for mission drift and ethical compromise

**Organizational Control:**
- Access restricted to verified missionary organizations
- Terms of Service prohibit law enforcement use
- Government agencies explicitly excluded from access
- Organizational vetting process validates missionary status

**Legal Protection:**
- Closed-source license prevents unauthorized use
- Legal agreements prohibit redistribution
- DMCA and copyright protections enforced

---

### Scenario 4: Data Exfiltration or Resale
**Risk:** Exporting platform data for external use or commercial purposes.

**Why It's Prohibited:**
- Proprietary data and enrichment
- Violates licensing and terms of service
- Undermines security of other users

**Technical Prevention:**
- API rate limiting prevents bulk export
- No bulk export features (intentionally omitted)
- Audit logging tracks all data access
- Download features limited and logged

**Detection:**
- Unusual download patterns flagged
- Large query volumes trigger alerts
- Audit log analysis for exfiltration patterns

---

### Scenario 5: Category or Region Abuse
**Risk:** Using platform to monitor specific ethnic, religious, or political groups.

**Why It's Prohibited:**
- Discriminatory monitoring violates ethics
- Potential for targeted harassment or surveillance
- Contradicts missionary values of love and respect

**Organizational Control:**
- Organization settings allow category filtering
- Administrators can disable sensitive categories
- Audit logs track category focus patterns
- Unusual patterns trigger manual review

**Technical Capability:**
- `organization_settings.exclude_regions` - Disable specific regions
- `organization_settings.alert_categories` - Limit alert categories
- Custom category filtering per organization

---

## Technical Safeguards

### 1. Data Model Design
**Events Are GLOBAL, Not Org-Scoped:**
- Prevents creation of private dossiers on individuals
- All events are shared, aggregated intelligence
- No private "watch lists" of people

**Dossiers Are Org-Scoped:**
- Organizations create dossiers on locations, topics, organizations
- No PII or individual tracking in dossier model
- Field-level validation prevents misuse

### 2. No Real-Time Capabilities
**Intentional Delays:**
- Event ingestion intervals (15-30 minutes minimum)
- No streaming or real-time feed access
- No "live" tactical awareness features

**Why:** Prevents use as tactical or operational tool.

### 3. Audit Logging
**Comprehensive Activity Tracking:**
- Every create, update, delete, view logged
- User, timestamp, IP, action type recorded
- Permanent, tamper-resistant audit trail

**Use Cases:**
- Detect unusual access patterns
- Investigate potential misuse
- Accountability for administrators

**See:** `backend/models/audit.py`, `backend/routers/audit.py`

### 4. Role-Based Access Control
**User Roles:**
- **Viewer:** Read-only access, no data modification
- **Analyst:** Create dossiers, provide feedback
- **Admin:** Full access, settings management

**Why:** Limits blast radius of compromised accounts.

### 5. Multi-Tenant Isolation
**Organization Boundaries:**
- Each organization sees only its own dossiers/watchlists
- Events are global but dossiers are private
- No cross-tenant data leakage

**Technical Implementation:**
- All org-scoped queries filtered by `organization_id`
- User-org relationships enforce boundaries
- Database-level foreign keys prevent orphaned data

### 6. Input Validation & Sanitization
**API-Level Validation:**
- Pydantic schemas validate all inputs
- SQL injection prevention (ORM-based queries)
- XSS prevention (output encoding)

**Rate Limiting:**
- API endpoints rate-limited per user/org
- Prevents brute force and DOS
- Configurable per organization

---

## Organizational Controls

### 1. Access Vetting
**Organization Onboarding:**
- Manual verification of missionary status
- Legal agreements required
- Terms of Service acceptance
- Background check for organization leadership (optional)

### 2. Training and Education
**Required Training:**
- Ethical OSINT principles
- Platform limitations and purpose
- Prohibited use cases
- Reporting suspicious activity

### 3. Terms of Service
**Key Clauses:**
- OSINT-only data sources permitted
- No targeting or tactical use
- No law enforcement or intelligence use
- No data exfiltration or resale
- Violation triggers immediate termination

### 4. Administrator Responsibilities
**Organization Admins Must:**
- Monitor user activity via audit logs
- Disable misused features (categories, regions)
- Report suspicious activity to platform maintainers
- Ensure user training compliance

### 5. Data Retention Policies
**Organization-Configurable:**
- `organization_settings.event_retention_days` - Auto-delete old events
- `organization_settings.audit_log_retention_days` - Audit trail retention
- Default: Events retained indefinitely, audit logs 365 days

**Why:** Limits data exposure in breach scenarios.

---

## Monitoring and Auditing

### 1. Automated Monitoring
**Metrics Tracked:**
- API request volumes per user/org
- Query patterns (unusual categories, regions)
- Data export/download volumes
- Failed authentication attempts
- Privilege escalation attempts

**Alerts Triggered On:**
- High-volume queries (potential scraping)
- Unusual time-of-day access
- Geographic access anomalies (VPN/Tor)
- Repeated failed authentications

### 2. Manual Review
**Quarterly Audits:**
- Review audit logs for top users by volume
- Analyze query patterns for misuse indicators
- Validate organization compliance with ToS
- Interview admins about user behavior

### 3. Audit Log API
**Admin Access:**
- `GET /audit/logs` - Retrieve filtered logs
- `GET /audit/stats` - Aggregate statistics
- Filtered by user, action type, time period

**Use Cases:**
- Investigate suspicious activity
- Compliance reporting
- Incident response

---

## Incident Response

### 1. Suspected Misuse
**Immediate Actions:**
1. Suspend user/organization access
2. Review audit logs for scope of activity
3. Preserve evidence (logs, database snapshots)
4. Notify organization administrator
5. Escalate to platform maintainers

### 2. Confirmed Misuse
**Response Steps:**
1. Terminate user/organization access permanently
2. Legal review for ToS violation remedies
3. Report to law enforcement if criminal activity suspected
4. Document incident for future prevention
5. Update safeguards if new attack vector identified

### 3. Data Breach
**Immediate Actions:**
1. Isolate affected systems
2. Identify scope and data exposed
3. Notify affected organizations (GDPR/legal requirements)
4. Preserve forensic evidence
5. Engage security consultants

**Long-Term Actions:**
1. Root cause analysis
2. Security posture improvements
3. User notification and guidance
4. Regulatory reporting (if required)

---

## Legal and Compliance

### 1. Licensing
**Closed-Source License:**
- All Rights Reserved
- No redistribution or derivative works
- Access granted only via Terms of Service
- DMCA and copyright protections enforced

**See:** `LICENSE` file in repository root.

### 2. Terms of Service
**Key Legal Protections:**
- Defines permitted and prohibited use
- Liability limitations
- Indemnification clauses
- Dispute resolution process

### 3. Data Protection
**GDPR Compliance (where applicable):**
- Events are de-identified (no PII)
- User data (emails, names) minimized
- Data retention policies configurable
- Right to deletion (user accounts)

**Note:** Platform does not store PII of event subjects, only public event data.

### 4. Ethical Guidelines
**Missionary Context:**
- Data used only for safety and awareness
- No targeting of individuals or groups
- Respect for human dignity and rights
- Commitment to non-violence and peace

---

## Summary of Safeguards

| Risk | Technical Control | Organizational Control | Detection Method |
|------|------------------|----------------------|-----------------|
| Individual Tracking | No PII in data model | ToS prohibition | Audit log analysis |
| Tactical Use | No real-time features | Missionary vetting | Query pattern analysis |
| LE/Intelligence Use | Access restrictions | Org vetting process | Manual review |
| Data Exfiltration | Rate limiting, no bulk export | ToS prohibition | Volume alerts |
| Category Abuse | Category filtering | Admin monitoring | Audit logs |

---

## Contact for Security Issues

**Report suspected misuse or security vulnerabilities to:**
- Email: security@goodshepherd.example (replace with actual contact)
- Escalation: Platform administrators

**Do NOT disclose vulnerabilities publicly.** Coordinate disclosure responsibly.

---

**This document is living and should be updated as:**
- New risks are identified
- Technical safeguards are enhanced
- Organizational policies evolve
- Incident response procedures are tested

**Last Review:** 2025-11-25
**Next Review:** 2026-02-25 (Quarterly)
