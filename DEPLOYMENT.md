# Deployment Guide - The Good Shepherd

## Production Deployment Guide

This guide covers deploying The Good Shepherd OSINT intelligence platform to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Security Considerations](#security-considerations)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System:** Linux (Ubuntu 20.04+ or CentOS 8+ recommended)
- **CPU:** Minimum 2 cores, 4+ cores recommended
- **RAM:** Minimum 4GB, 8GB+ recommended
- **Storage:** Minimum 20GB SSD, 50GB+ recommended
- **Network:** Stable internet connection for OSINT data ingestion

### Software Requirements

- Docker 20.10+ and Docker Compose 1.29+
- PostgreSQL 15+ with PostGIS 3.3+
- Redis 6.2+
- Nginx or similar reverse proxy (for production)
- SSL/TLS certificates (Let's Encrypt recommended)

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://goodshepherd:SECURE_PASSWORD@postgres:5432/goodshepherd
POSTGRES_USER=goodshepherd
POSTGRES_PASSWORD=SECURE_PASSWORD_HERE
POSTGRES_DB=goodshepherd

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Authentication
JWT_SECRET_KEY=GENERATE_SECURE_RANDOM_STRING_HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# LLM Configuration (OpenAI)
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Worker Configuration
RSS_WORKER_INTERVAL_MINUTES=30
NEWS_WORKER_INTERVAL_MINUTES=60
FUSION_WORKER_INTERVAL_MINUTES=120

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# Environment
ENVIRONMENT=production
```

### Generating Secure Secrets

```bash
# Generate JWT secret key
openssl rand -hex 32

# Generate database password
openssl rand -base64 32
```

## Docker Deployment

### Production Docker Compose

Create or update `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/monitoring/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m workers.rss_worker
    env_file:
      - ./backend/.env
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Deployment Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd Goodshepherd

# 2. Configure environment
cp backend/.env.example backend/.env
nano backend/.env  # Edit with your production values

# 3. Build images
docker-compose -f docker-compose.prod.yml build

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Create initial admin user (optional)
docker-compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py

# 7. Verify deployment
curl http://localhost:8000/monitoring/health/detailed
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.20+
- kubectl configured
- Persistent volume provisioner
- Ingress controller (nginx-ingress recommended)

### ConfigMap for Environment Variables

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: goodshepherd-config
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  ENVIRONMENT: "production"
```

### Secret for Sensitive Data

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: goodshepherd-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/goodshepherd"
  JWT_SECRET_KEY: "your-secret-key"
  OPENAI_API_KEY: "sk-your-key"
```

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: goodshepherd-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: goodshepherd-backend
  template:
    metadata:
      labels:
        app: goodshepherd-backend
    spec:
      containers:
      - name: backend
        image: goodshepherd-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: goodshepherd-config
        - secretRef:
            name: goodshepherd-secrets
        livenessProbe:
          httpGet:
            path: /monitoring/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /monitoring/health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Database Setup

### Initial Migration

```bash
# Inside backend container or with proper DATABASE_URL set
alembic upgrade head
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U goodshepherd goodshepherd > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose exec -T postgres psql -U goodshepherd goodshepherd < backup.sql
```

### Database Optimization

```sql
-- Create indices for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_org_timestamp ON events(organization_id, timestamp DESC);

-- Enable PostGIS spatial indices
CREATE INDEX IF NOT EXISTS idx_events_location ON events USING GIST(location);

-- Analyze tables for query optimization
ANALYZE events;
ANALYZE dossiers;
ANALYZE users;
```

## Monitoring & Health Checks

### Health Check Endpoints

- **Liveness Probe:** `GET /monitoring/health/live`
  - Returns 200 if application is alive
  - Use for Kubernetes liveness probe

- **Readiness Probe:** `GET /monitoring/health/ready`
  - Returns 200 if ready to serve traffic
  - Checks database connectivity
  - Use for Kubernetes readiness probe

- **Detailed Health:** `GET /monitoring/health/detailed`
  - Comprehensive health status
  - Component-level diagnostics
  - Use for monitoring dashboards

- **Metrics:** `GET /monitoring/metrics`
  - Application metrics
  - Event counts, user counts
  - Performance indicators

### Logging

Logs are output in structured JSON format (when `LOG_FORMAT=json`):

```bash
# View logs
docker-compose logs -f backend

# Filter by log level
docker-compose logs backend | grep '"level":"error"'

# Search for specific request
docker-compose logs backend | grep '"request_id":"<uuid>"'
```

### Application Monitoring

Integrate with monitoring solutions:

- **Prometheus:** Metrics endpoint at `/monitoring/metrics`
- **Grafana:** Create dashboards using metrics
- **ELK Stack:** Ship JSON logs to Elasticsearch
- **Sentry:** Add Sentry SDK for error tracking

## Security Considerations

### Network Security

```nginx
# Nginx reverse proxy configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### Database Security

- Use strong passwords
- Enable SSL/TLS for database connections
- Restrict database access to application only
- Regular security updates
- Implement row-level security if multi-tenant

### API Security

- JWT tokens with secure secret keys
- HTTPS only in production
- CORS properly configured
- Rate limiting (implement if needed)
- Input validation on all endpoints

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose exec -T postgres pg_dump -U goodshepherd goodshepherd | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days of backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://your-bucket/backups/
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### Recovery Procedure

```bash
# 1. Stop services
docker-compose down

# 2. Restore database
gunzip < backup_20240115_020000.sql.gz | docker-compose exec -T postgres psql -U goodshepherd goodshepherd

# 3. Restart services
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/monitoring/health/detailed
```

## Troubleshooting

### Common Issues

**Issue:** Database connection refused
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection
docker-compose exec backend python -c "from backend.core.database import check_db_connection; print(check_db_connection())"
```

**Issue:** High memory usage
```bash
# Check container resource usage
docker stats

# Increase container limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

**Issue:** Worker not processing events
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Verify worker status
docker-compose exec backend python -c "from workers.rss_worker import main; main()"
```

### Performance Tuning

**PostgreSQL:**
```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- Reload configuration
SELECT pg_reload_conf();
```

**Application:**
```python
# Increase database connection pool
# In backend/core/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Apply migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart
```

### Database Maintenance

```sql
-- Vacuum database
VACUUM ANALYZE;

-- Reindex tables
REINDEX DATABASE goodshepherd;
```

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [documentation-url]
- Email: support@yourdomain.com

---

**Version:** 0.8.0
**Last Updated:** 2025
