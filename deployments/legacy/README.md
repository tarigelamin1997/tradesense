# Legacy Docker and Compose variants

Earlier experiments and environment-specific variants, kept for reference. **Not used by CI or production.**

| Folder | Contents |
|---|---|
| `docker/` | Alternate Dockerfiles (`*.fixed`, Railway, siege load-test, test) and an old `railway.toml` variant |
| `compose/` | Alternate docker-compose files (staging, production, monitoring, performance, backup, …) |

Paths inside the compose files are relative to the repository root, so run them from the root with `--project-directory`:

```bash
docker compose --project-directory . -f deployments/legacy/compose/docker-compose.monitoring.yml up -d
```

The maintained compose files remain in the repository root:

| File | Purpose |
|---|---|
| `docker-compose.simple.yml` | Full local stack (API + frontend + Postgres + Redis) |
| `docker-compose.db-only.yml` | Postgres + Redis only, for running the app natively |
| `docker-compose.microservices.yml` | Gateway + auth + trading microservices locally |
