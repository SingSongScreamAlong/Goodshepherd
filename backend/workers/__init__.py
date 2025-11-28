"""Background workers for Good Shepherd.

Workers:
- alert_worker: Processes events and triggers notifications
- digest_worker: Sends scheduled digest emails
- ingestion_worker: Fetches data from external sources

Run individually:
    python -m backend.workers.alert_worker
    python -m backend.workers.digest_worker
    python -m backend.workers.ingestion_worker
"""
