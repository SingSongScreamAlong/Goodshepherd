# Good Shepherd Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL with PostGIS extension
- Redis

---

## Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/goodshepherd.git
cd goodshepherd

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Required Environment Variables

```bash
# Database
POSTGRES_PASSWORD=secure_password

# Admin Access
ADMIN_API_KEY=your_secure_admin_key

# Twilio (SMS/WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_ADDRESS=alerts@yourdomain.com

# Intelligence Sources
ACLED_API_KEY=your_acled_key
ACLED_EMAIL=your_email@example.com

# Search
MEILI_MASTER_KEY=your_meilisearch_key

# Object Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=secure_password
```

### 3. Start Services

```bash
cd infrastructure
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:3000
```

---

## Production Deployment

### Using Docker Compose

```bash
# Build and start in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f backend-api
```

### Using Kubernetes

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: goodshepherd-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: goodshepherd-api
  template:
    metadata:
      labels:
        app: goodshepherd-api
    spec:
      containers:
      - name: api
        image: goodshepherd-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: goodshepherd-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

## Service Configuration

### PostgreSQL with PostGIS

```bash
# Create database with PostGIS
docker exec -it postgres psql -U goodshepherd -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Redis

Redis is used for:
- Event queue processing
- Rate limiting
- Session caching

No special configuration required for basic usage.

### Meilisearch

Used for full-text event search.

```bash
# Create index
curl -X POST 'http://localhost:7700/indexes' \
  -H 'Authorization: Bearer your_master_key' \
  -H 'Content-Type: application/json' \
  -d '{"uid": "events", "primaryKey": "id"}'
```

### Caddy (Reverse Proxy)

The included Caddyfile handles:
- HTTPS with automatic certificates
- WebSocket proxying
- Static file serving

```caddyfile
# infrastructure/Caddyfile
yourdomain.com {
    reverse_proxy /api/* backend-api:8000
    reverse_proxy /ws backend-api:8000
    reverse_proxy frontend:3000
}
```

---

## SSL/TLS Configuration

### With Caddy (Automatic)

Caddy automatically obtains and renews Let's Encrypt certificates.

```caddyfile
yourdomain.com {
    # Automatic HTTPS
    reverse_proxy backend-api:8000
}
```

### With Nginx (Manual)

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /api/ {
        proxy_pass http://backend-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend-api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.override.yml
services:
  backend-api:
    deploy:
      replicas: 3
```

### Load Balancing

Use a load balancer (HAProxy, Nginx, or cloud LB) in front of API instances.

**Important:** WebSocket connections are sticky - use IP hash or cookie-based session affinity.

```nginx
upstream backend {
    ip_hash;  # Sticky sessions for WebSocket
    server backend-api-1:8000;
    server backend-api-2:8000;
    server backend-api-3:8000;
}
```

---

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/health

# WebSocket stats
curl http://localhost:8000/api/ws/stats

# Database connectivity
docker exec postgres pg_isready -U goodshepherd
```

### Logging

```bash
# View API logs
docker-compose logs -f backend-api

# View all logs
docker-compose logs -f
```

### Metrics (Prometheus)

Add to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'goodshepherd'
    static_configs:
      - targets: ['backend-api:8000']
    metrics_path: '/metrics'
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup
docker exec postgres pg_dump -U goodshepherd goodshepherd > backup.sql

# Restore
docker exec -i postgres psql -U goodshepherd goodshepherd < backup.sql
```

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron
DATE=$(date +%Y%m%d)
docker exec postgres pg_dump -U goodshepherd goodshepherd | gzip > /backups/goodshepherd_$DATE.sql.gz

# Keep last 30 days
find /backups -name "goodshepherd_*.sql.gz" -mtime +30 -delete
```

---

## Troubleshooting

### API Not Starting

```bash
# Check logs
docker-compose logs backend-api

# Common issues:
# - Database not ready: Wait for postgres healthcheck
# - Missing env vars: Check .env file
# - Port conflict: Change port mapping
```

### WebSocket Connection Issues

```bash
# Check if WebSocket endpoint is accessible
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/ws

# Common issues:
# - Proxy not configured for WebSocket upgrade
# - Firewall blocking WebSocket port
# - SSL termination issues
```

### Database Connection Issues

```bash
# Test connection
docker exec backend-api python -c "
from backend.database.session import engine
import asyncio
async def test():
    async with engine.connect() as conn:
        print('Connected!')
asyncio.run(test())
"
```

### Email Not Sending

```bash
# Test SMTP connection
docker exec backend-api python -c "
import smtplib
server = smtplib.SMTP('smtp.example.com', 587)
server.starttls()
server.login('user', 'pass')
print('SMTP OK')
"
```

---

## Security Checklist

- [ ] Change default passwords
- [ ] Set strong ADMIN_API_KEY
- [ ] Enable HTTPS in production
- [ ] Configure firewall rules
- [ ] Enable database SSL
- [ ] Rotate API keys regularly
- [ ] Set up log monitoring
- [ ] Configure rate limiting
- [ ] Enable CORS restrictions
- [ ] Set up intrusion detection

---

## Environment Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `ADMIN_API_KEY` | Yes | Admin authentication key |
| `TWILIO_ACCOUNT_SID` | No | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `TWILIO_FROM_NUMBER` | No | SMS sender number |
| `TWILIO_WHATSAPP_NUMBER` | No | WhatsApp sender number |
| `SMTP_HOST` | No | SMTP server hostname |
| `SMTP_PORT` | No | SMTP server port (default: 587) |
| `SMTP_USERNAME` | No | SMTP username |
| `SMTP_PASSWORD` | No | SMTP password |
| `SMTP_FROM_ADDRESS` | No | Email sender address |
| `ACLED_API_KEY` | No | ACLED API key |
| `ACLED_EMAIL` | No | ACLED registered email |
| `MEILI_MASTER_KEY` | No | Meilisearch master key |
| `MEILI_HTTP_ADDR` | No | Meilisearch URL |
