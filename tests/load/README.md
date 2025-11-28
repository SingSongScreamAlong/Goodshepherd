# Load Testing for Good Shepherd API

This directory contains load testing scripts using [Locust](https://locust.io/).

## Installation

```bash
pip install locust
```

## Running Load Tests

### Interactive Mode (Web UI)

Start the Locust web interface:

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to configure and start the test.

### Headless Mode (CLI)

Run a quick load test without the web UI:

```bash
# 100 users, spawn rate 10/sec, run for 60 seconds
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --headless -u 100 -r 10 --run-time 60s
```

### With HTML Report

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --headless -u 100 -r 10 --run-time 60s \
       --html=load_test_report.html
```

## Test Scenarios

The load test includes three user types:

### GoodShepherdUser (weight: 10)
Regular API users performing typical operations:
- Health checks (high frequency)
- List geofences (medium frequency)
- Update location (medium frequency)
- Get threat level (lower frequency)
- Get nearby threats (low frequency)

### AdminUser (weight: 1)
Admin users performing management tasks:
- Create geofences
- List subscriptions
- Delete geofences (cleanup)

### WebSocketUser (weight: 2)
Users checking WebSocket connectivity:
- WebSocket stats endpoint

## Performance Targets

| Endpoint | Target p95 | Target RPS |
|----------|------------|------------|
| GET /api/health | < 50ms | 1000+ |
| GET /api/geofences | < 100ms | 500+ |
| POST /api/location/update | < 200ms | 200+ |
| GET /api/location/{id}/threat-level | < 100ms | 300+ |

## Environment Variables

Set `ADMIN_API_KEY` on the server to match the test:

```bash
export ADMIN_API_KEY=test-admin-key
```

## Tips

1. **Start small**: Begin with 10-20 users and gradually increase
2. **Monitor resources**: Watch CPU, memory, and database connections
3. **Check logs**: Look for errors and slow queries
4. **Test rate limiting**: Verify rate limits work under load
5. **Database**: Ensure database connection pooling is configured
