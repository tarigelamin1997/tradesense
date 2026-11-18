# Configuration

All configuration is via environment variables. **This page lists names and purpose only. Real values belong in Railway / Vercel variable settings or a local, untracked `.env` — never in the repository.**

Start from the template:

```bash
cp .env.example .env
```

Generate secrets with:

```bash
openssl rand -hex 32
```

---

## Microservices (production)

### Shared

| Variable | Services | Purpose |
|---|---|---|
| `PORT` | all | Port to bind; injected by Railway |
| `DATABASE_URL` | auth, trading, analytics, billing, ai | PostgreSQL connection string for the service's own database |
| `AUTH_SERVICE_URL` | trading, analytics, billing, ai, gateway | Base URL of the auth service, used for token verification |

### gateway

| Variable | Purpose |
|---|---|
| `CORS_ORIGINS` | Comma-separated list of allowed browser origins (exact scheme + host) |
| `AUTH_SERVICE_URL` | Upstream for `/auth/*` |
| `TRADING_SERVICE_URL` | Upstream for `/trades/*` |
| `ANALYTICS_SERVICE_URL` | Upstream for `/analytics/*` |
| `MARKET_DATA_SERVICE_URL` | Upstream for `/market-data/*` |
| `BILLING_SERVICE_URL` | Upstream for `/billing/*` |
| `AI_SERVICE_URL` | Upstream for `/ai/*` |

### auth

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | HMAC key used to sign and verify access tokens. Secret. If unset, a random per-process key is used (tokens break on restart) and a critical error is logged. |

### analytics / ai

| Variable | Purpose |
|---|---|
| `TRADING_SERVICE_URL` | Read access to trade data |
| `ANALYTICS_SERVICE_URL` | (ai only) analytics data for insights |
| `OPENAI_API_KEY` | (ai only) OpenAI API key. Secret. |

### market-data

| Variable | Purpose |
|---|---|
| `REDIS_URL` | Redis connection string for the quote cache |

### billing

| Variable | Purpose |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe API secret key. Secret. |
| `STRIPE_PRICE_BASIC` | Stripe Price ID for the Basic plan |
| `STRIPE_PRICE_PRO` | Stripe Price ID for the Pro plan |
| `STRIPE_PRICE_PREMIUM` | Stripe Price ID for the Premium plan |
| `STRIPE_WEBHOOK_SECRET` | Signing secret of the Stripe webhook endpoint (`whsec_…`). Required: without it all webhooks are rejected. Secret. |

---

## Consolidated backend (`src/backend/`)

### Core

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` / `staging` / `production`. `production` enables `Secure` auth cookies |
| `DEBUG` | Verbose errors and debug behaviour; `false` in production |
| `PORT` | Port to bind |
| `LOG_LEVEL` | Logging level (`INFO`, `DEBUG`, …) |
| `LOG_FILE` | Optional log file path |
| `FRONTEND_URL` | Frontend base URL, used in emails and OAuth redirects |
| `CORS_ORIGINS_STR` | Comma-separated list of allowed browser origins |
| `SKIP_DB_INIT` | Read by `start.sh`: skip database initialisation on startup (faster cold starts) |
| `ENABLE_TASK_CLEANUP` | Enable periodic background cleanup tasks |

### Security

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | HMAC key for signing access tokens. Secret. Falls back to `SECRET_KEY` if unset |
| `SECRET_KEY` | Application secret for other signing/encryption needs. Secret |
| `MASTER_ENCRYPTION_KEY` | Key for encrypting stored third-party credentials. Secret |
| `JWT_ALGORITHM` | Token signing algorithm (default `HS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 30) |

> If neither `JWT_SECRET_KEY` nor `SECRET_KEY` is set, a random key is generated at startup. Tokens then stop validating after every restart and across replicas — always set it explicitly.

### Database & cache

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (preferred) |
| `DATABASE_PRIVATE_URL` | Railway private-network connection string; used when present |
| `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | Railway-style discrete Postgres settings (alternative to `DATABASE_URL`) |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Generic discrete Postgres settings (alternative to `DATABASE_URL`) |
| `REDIS_URL` | Redis connection string (cache, rate limiting) |

### Integrations

| Variable | Purpose |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Verifies Stripe webhook signatures |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth sign-in |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | GitHub OAuth sign-in |
| `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT` | Microsoft OAuth sign-in |
| `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | LinkedIn OAuth sign-in |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | SMS delivery for MFA codes and trading alerts |

---

## Frontend (`frontend/`, Vercel)

Values are inlined at build time — redeploy after changing them.

| Variable | Purpose |
|---|---|
| `PUBLIC_API_URL` | Gateway base URL (HTTPS) |
| `PUBLIC_WS_URL` | Gateway WebSocket URL (WSS) |
| `VITE_API_BASE_URL` | API base URL used by auth and status components; set to the gateway URL |
| `VITE_API_URL` | Legacy alias of `VITE_API_BASE_URL` |
| `VITE_WS_URL` | Legacy alias of `PUBLIC_WS_URL` |
| `VITE_USE_GATEWAY` | `false` to call services directly instead of through the gateway (debugging only) |

---

## CI/CD (GitHub Actions secrets)

| Secret | Purpose |
|---|---|
| `RAILWAY_TOKEN` | Deploy services to Railway |
| `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | Deploy the frontend to Vercel |

---

## Rules

- Never commit `.env` files or real values. Use `.env.example` with empty values as the template.
- Use a different `JWT_SECRET_KEY` per environment (dev, staging, prod).
- Rotate any secret that has ever appeared in a commit, log or chat — removing it from the latest commit does not remove it from git history.
