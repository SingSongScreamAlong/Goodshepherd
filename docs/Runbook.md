# Good Shepherd Runbook

## Purpose
This runbook is the quick-reference guide for operating the Good Shepherd situational awareness platform on a single DigitalOcean droplet.

## Contacts
- **Primary Ops**: ops@missions.org
- **Escalation**: security@missions.org

## Daily Checklist
- **Check feeds**: Ensure ingestion worker logs show updates in last 6 hours.
- **Verify API**: `curl -f https://yourdomain.com/healthz`
- **Review alerts**: Confirm Matrix/email alerts match events in dashboard.
- **Database size**: Ensure Postgres volume <80% capacity (`docker exec db du -sh /var/lib/postgresql/data`).

## Weekly Checklist
- **Apply OS updates**: `apt update && apt upgrade -y` (droplet).
- **Rotate logs**: Archive worker/API logs to MinIO (`mc cp` commands).
- **Backup**: Trigger snapshot (`pg_dump` to MinIO; download to local).
- **Test restore**: Restore latest snapshot to staging Postgres (optional but recommended).

## Incident Response
- **Service down**: `docker compose ps` -> identify crashed container -> `docker compose logs <service>` -> restart `docker compose restart <service>`.
- **High CPU/memory**: `docker stats`; scale vertically or throttle ingestion interval (`FEED_POLL_INTERVAL` env var).
- **Redis backlog**: Check stream size (`xlen events.raw`). If >10k pending, add worker replicas temporarily (`docker compose up -d --scale worker=2`).
- **Ingress failure**: Validate feed URLs; ensure DNS resolution. Switch to backup feed list in `.env.backup`.

## Deployment Steps
1. `ssh ops@droplet`
2. `cd ~/good_shepherd/good_shepherd_repo`
3. `git pull` (or sync latest release archive)
4. `docker compose build`
5. `docker compose up -d`
6. `docker compose logs -f` (verify healthy startup)

## Rolling Back
1. `docker compose down`
2. `git checkout <previous_tag>`
3. `docker compose up -d`
4. Confirm `/healthz` responds; check frontend.

## Backups
- **Postgres**: Nightly `pg_dump` to `minio://backups/postgres/<date>.sql.gz`.
- **MinIO**: Weekly sync to DigitalOcean Spaces (`mc mirror` command).
- **Configs**: Keep `.env` in Bitwarden vault; never commit.

## Secrets Management
- `.env` stored at `/root/good_shepherd/.env`; symlink into repo for compose.
- Update secrets via `nano .env` -> `docker compose up -d` to propagate.
- Rotate credentials quarterly or when personnel changes occur.

## Monitoring & Alerts
- **Health checks**: UptimeRobot ping to `/healthz` every 5 minutes.
- **Log streaming**: Optional Elastic/Vector or `docker logs -f` into `tailon` for remote view.
- **Metrics**: Add Prometheus scraping once `/metrics` shipped (Phase 2).

## When to Call for Help
- Data ingestion halted for >12 hours without clear fix.
- Security incident suspected (data tampering, unauthorized access).
- Infrastructure costs >$40/mo unexpectedly.
- Critical path bug preventing alerts or map rendering.
