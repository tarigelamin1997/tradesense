# Deployment

| Component | Platform | Source directory | Deployed as |
|---|---|---|---|
| Frontend | Vercel | `frontend/` | SvelteKit app (`adapter-vercel`) |
| API gateway + 6 services | Railway | `services/<name>/` | One Railway service per directory, built from its `Dockerfile` |
| PostgreSQL | Railway | — | Managed Postgres, one per stateful service |
| Redis | Railway | — | Managed Redis for market-data cache |

Railway service names follow the pattern `tradesense-<name>`: `tradesense-gateway`, `tradesense-auth`, `tradesense-trading`, `tradesense-analytics`, `tradesense-market-data`, `tradesense-billing`, `tradesense-ai`.

---

## 1. Automated deployment (default)

`.github/workflows/pipeline.yml` is the single CI/CD pipeline.

| Job | Runs on | Blocks deploy? |
|---|---|---|
| Secret scan (gitleaks, new commits only) | PRs + `main` | Yes |
| Backend tests, one job per service | PRs + `main` | Yes |
| Frontend build | PRs + `main` | Yes |
| Frontend unit tests + type check | PRs + `main` | No (advisory; known failures) |
| Deploy each service to Railway (`railway up --ci`) | `main` only, when `RAILWAY_TOKEN` is set | — |
| Deploy frontend to Vercel | `main` only, when `VERCEL_TOKEN` is set | — |
| Gateway health check (retries for ~2 min) | after Railway deploy, when `GATEWAY_URL` is set | — |

If a deploy token is missing, the deploy job is **skipped with a warning annotation** rather than reported as successful.

Required configuration (Settings → Secrets and variables → Actions):

| Name | Kind | Used for |
|---|---|---|
| `RAILWAY_TOKEN` | Secret | Railway CLI deploys (project token) |
| `VERCEL_TOKEN` | Secret | Vercel CLI deploys |
| `VERCEL_ORG_ID` | Secret | Vercel project scope |
| `VERCEL_PROJECT_ID` | Secret | Vercel project scope |
| `GATEWAY_URL` | Variable | Post-deploy health check, e.g. `https://<gateway-domain>` |

Older workflows are kept in `.github/workflows-archive/` for reference and do not run.

---

## 2. First-time setup

### 2.1 Railway (backend)

1. Create a Railway project.
2. Add data stores: one **PostgreSQL** for each of auth, trading, analytics, billing and ai, and one **Redis** for market-data. (A single shared Postgres also works for small environments; each service creates its own tables.)
3. For each directory in `services/` create a Railway service named `tradesense-<name>` and either link it to the GitHub repo with **Root Directory** = `services/<name>`, or deploy it from the CLI:

   ```bash
   cd services/auth
   railway link            # select the project and tradesense-auth
   railway up --service tradesense-auth
   ```

   Each service's `railway.toml` sets the Dockerfile builder, the `/health` health check and an on-failure restart policy. No start command is needed.
4. Set environment variables per service. Full list in [configuration.md](configuration.md). Minimum:

   | Service | Variables |
   |---|---|
   | auth | `DATABASE_URL`, `JWT_SECRET_KEY` |
   | billing | also `STRIPE_SECRET_KEY`, `STRIPE_PRICE_*`, `STRIPE_WEBHOOK_SECRET` |
   | trading, analytics, billing, ai | `DATABASE_URL`, `AUTH_SERVICE_URL` (+ service-specific keys) |
   | market-data | `REDIS_URL` |
   | gateway | `CORS_ORIGINS` and every `*_SERVICE_URL` |

   Use Railway variable references (for example `${{Postgres.DATABASE_URL}}`) instead of pasting connection strings.
5. Deploy services before the gateway, then set the gateway's `*_SERVICE_URL` variables to the deployed service URLs and redeploy the gateway.

### 2.2 Vercel (frontend)

1. Import the GitHub repository in Vercel.
2. Project settings:

   | Setting | Value |
   |---|---|
   | Framework preset | SvelteKit |
   | Root directory | `frontend` |
   | Build command | `npm run build` |
   | Install command | `npm install` |
   | Node.js version | 18 or later |

3. Environment variables — all point at the **gateway** URL:

   | Variable | Value |
   |---|---|
   | `PUBLIC_API_URL` | `https://<gateway-domain>` |
   | `PUBLIC_WS_URL` | `wss://<gateway-domain>` |
   | `VITE_API_BASE_URL` | `https://<gateway-domain>` |

4. Deploy, then add the Vercel production domain (and any custom domain) to the gateway's `CORS_ORIGINS` and redeploy the gateway.

---

## 3. Database migrations

Services create their tables on startup. For schema changes managed by Alembic (consolidated backend), run migrations against the target database:

```bash
railway run --service <service> "alembic upgrade head"
```

---

## 4. Verify a deployment

```bash
GATEWAY=https://<gateway-domain>

curl -f $GATEWAY/health                       # gateway + aggregated service health
curl -f $GATEWAY/services                     # registered downstream services

# CORS preflight from the frontend origin
curl -si -X OPTIONS $GATEWAY/auth/token \
  -H "Origin: https://<frontend-domain>" \
  -H "Access-Control-Request-Method: POST" | grep -i access-control-allow-origin
```

Then sign up and log in through the frontend and confirm the dashboard loads trades.

---

## 5. Operations

| Task | Command / location |
|---|---|
| Service logs | `railway logs --service tradesense-<name>` |
| Restart a service | Railway dashboard → service → Deployments → Redeploy |
| Inspect variables | `railway variables --service tradesense-<name>` |
| Roll back backend | Railway dashboard → Deployments → previous deployment → Redeploy |
| Roll back frontend | Vercel dashboard → Deployments → previous deployment → Promote to Production |

### Troubleshooting

| Symptom | Check |
|---|---|
| Browser shows CORS error | Frontend origin missing from gateway `CORS_ORIGINS` (exact scheme + host, comma-separated, no trailing slash); redeploy gateway after changing it |
| `404` on `/auth/*` through gateway | Gateway `AUTH_SERVICE_URL` unset or wrong |
| `401` on every authenticated call | `JWT_SECRET_KEY` changed since the token was issued, or downstream service cannot reach `AUTH_SERVICE_URL` |
| Frontend calls `localhost:8000` in production | `VITE_API_BASE_URL` / `PUBLIC_API_URL` not set in Vercel; values are baked in at build time, so redeploy after setting them |
| Railway health check fails | Service must bind to `0.0.0.0:$PORT` and answer `GET /health` within 30 s |

---

## 6. Production checklist

- [ ] Unique, randomly generated `JWT_SECRET_KEY` / `SECRET_KEY` (≥ 32 bytes), set only in Railway
- [ ] `ENVIRONMENT=production` (enables `Secure` cookies)
- [ ] `CORS_ORIGINS` lists only real frontend origins
- [ ] Stripe live secret key, `STRIPE_PRICE_*` IDs and `STRIPE_WEBHOOK_SECRET` set on billing; `/billing/webhook` registered in Stripe
- [ ] Postgres backups enabled in Railway
- [ ] All `/health` endpoints green after deploy
