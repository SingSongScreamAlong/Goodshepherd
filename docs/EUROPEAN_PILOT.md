# Good Shepherd - European AOR Pilot Deployment

## Overview

This document outlines the deployment and operation of Good Shepherd for the European Area of Responsibility (AOR) pilot. The pilot focuses on providing threat intelligence and safety alerts for missionaries operating in European regions.

## Pilot Scope

### Geographic Coverage
- **Primary Regions**: Western Europe, Eastern Europe, Balkans
- **Border Regions**: Eastern borders (Poland, Baltic states), Mediterranean routes
- **Focus Countries**: Initial deployment in 5-10 countries based on missionary presence

### Data Sources
1. **EU Open Data Portal** - Government and public sector data
2. **GDACS** - Global Disaster Alert and Coordination System
3. **ECDC** - European Centre for Disease Prevention and Control
4. **Frontex** - European Border and Coast Guard Agency

## GDPR Compliance

### Legal Basis for Processing
- **Consent**: User-provided consent for data collection
- **Legitimate Interests**: Safety and security of missionaries
- **Vital Interests**: Emergency situations requiring immediate action

### Data Categories Processed
| Category | Retention Period | Purpose |
|----------|-----------------|---------|
| Basic Identity | 3 years | User account management |
| Location Data | 90 days | Safety check-ins, alerts |
| Behavioral Data | 1 year | App usage, preferences |
| Sensitive Data | 1 year | Health alerts (opt-in) |

### Data Subject Rights
Users can exercise the following rights through the app or by contacting the Data Protection Officer:
- **Right to Access** (Article 15)
- **Right to Rectification** (Article 16)
- **Right to Erasure** (Article 17)
- **Right to Restriction** (Article 18)
- **Right to Data Portability** (Article 20)
- **Right to Object** (Article 21)

### Data Protection Measures
- End-to-end encryption for sensitive data
- Pseudonymization of user identifiers
- Data minimization principles
- Regular security audits
- Incident response procedures

## Deployment Architecture

### Infrastructure
```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   API (3x)  │  │  Frontend   │  │   Worker    │         │
│  │   Pods      │  │   (2x)      │  │   (2x)      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│  ┌──────┴────────────────┴────────────────┴──────┐         │
│  │              Internal Services                 │         │
│  │  PostgreSQL │ Redis │ Meilisearch │ LibreTranslate      │
│  └────────────────────────────────────────────────┘         │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │              Monitoring Stack                   │         │
│  │  Elasticsearch │ Logstash │ Kibana │ Prometheus │        │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Scaling Configuration
- **API**: 3-10 replicas (HPA based on CPU/memory)
- **Frontend**: 2 replicas (static content)
- **Workers**: 2-5 replicas (based on queue depth)

## Operational Runbook

### Deployment Steps

1. **Create Namespace**
   ```bash
   kubectl apply -f infrastructure/kubernetes/namespace.yaml
   ```

2. **Deploy Secrets and ConfigMaps**
   ```bash
   # Update secrets with actual values first
   kubectl apply -f infrastructure/kubernetes/configmap.yaml
   ```

3. **Deploy Database and Cache**
   ```bash
   kubectl apply -f infrastructure/kubernetes/postgres.yaml
   kubectl apply -f infrastructure/kubernetes/redis.yaml
   ```

4. **Deploy Application**
   ```bash
   kubectl apply -f infrastructure/kubernetes/api-deployment.yaml
   kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
   ```

5. **Configure Ingress**
   ```bash
   kubectl apply -f infrastructure/kubernetes/ingress.yaml
   ```

6. **Deploy Monitoring**
   ```bash
   kubectl apply -f infrastructure/kubernetes/monitoring.yaml
   ```

### Health Checks

**API Health**
```bash
curl https://api.goodshepherd.example.com/health
```

**Database Connectivity**
```bash
kubectl exec -it deploy/goodshepherd-api -- python -c "from backend.database.session import test_connection; test_connection()"
```

**Source Connectivity**
```bash
kubectl exec -it deploy/goodshepherd-api -- python -c "from backend.sources.european import GDACSConnector; import asyncio; print(asyncio.run(GDACSConnector().get_alerts()))"
```

### Incident Response

#### High Alert Volume
1. Check source connectivity
2. Verify ML service status
3. Scale API replicas if needed
4. Review rate limiting configuration

#### Database Issues
1. Check PostgreSQL pod status
2. Verify connection pool settings
3. Review slow query logs
4. Consider read replica scaling

#### SMS Delivery Failures
1. Check Twilio/Vonage status
2. Verify API credentials
3. Check rate limits
4. Failover to backup provider

### Backup Procedures

**Database Backup**
```bash
kubectl exec -it postgres-0 -- pg_dump -U goodshepherd goodshepherd > backup.sql
```

**GDPR Data Export**
```bash
kubectl exec -it deploy/goodshepherd-api -- python -m backend.compliance.gdpr export --user-id <USER_ID>
```

## Monitoring and Alerting

### Key Metrics
| Metric | Warning | Critical |
|--------|---------|----------|
| API Response Time (p95) | > 500ms | > 2s |
| Error Rate | > 1% | > 5% |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Queue Depth | > 1000 | > 5000 |

### Alert Channels
- **PagerDuty**: Critical alerts (24/7)
- **Slack**: Warning alerts (#goodshepherd-alerts)
- **Email**: Daily summary reports

### Dashboards
- **Kibana**: Log analysis and search
- **Grafana**: Metrics and performance
- **Custom**: Threat intelligence overview

## Success Criteria

### Technical Metrics
- [ ] 99.9% uptime during pilot period
- [ ] < 500ms API response time (p95)
- [ ] < 1% error rate
- [ ] Successful processing of 1000+ events/day

### User Metrics
- [ ] 50+ active users during pilot
- [ ] 90%+ check-in completion rate
- [ ] < 5 minute alert delivery time
- [ ] Positive user feedback (NPS > 50)

### Compliance Metrics
- [ ] 100% GDPR request completion within 30 days
- [ ] Zero data breaches
- [ ] Successful security audit
- [ ] Complete audit trail

## Contacts

### Technical Team
- **On-Call**: oncall@goodshepherd.org
- **Engineering Lead**: engineering@goodshepherd.org

### Data Protection
- **DPO**: dpo@goodshepherd.org
- **GDPR Requests**: privacy@goodshepherd.org

### Emergency
- **Security Incidents**: security@goodshepherd.org
- **Escalation**: leadership@goodshepherd.org

## Appendix

### Environment Variables
See `infrastructure/.env.example` for complete list.

### API Documentation
Available at `/docs` endpoint when deployed.

### Source Code
Repository: https://github.com/SingSongScreamAlong/Goodshepherd
