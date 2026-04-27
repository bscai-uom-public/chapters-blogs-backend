# Chapters Blogs Backend Run and Deploy

## Runtime profiles

### Profile A: local direct API

- Caller talks directly to FastAPI on port `3003`.
- Auth usually tested with Bearer token flow.
- Useful for local development and debugging.

### Profile B: gateway-backed production

- Gateway/Auth layer sits in front of this service.
- Recommended for production traffic isolation and policy enforcement.

### Profile C: Vercel production (current)

- FastAPI is deployed as a Vercel Python function via `api/index.py` + `vercel.json`.
- Production URL: `https://chapters-blogs-backend.vercel.app`
- Environment variables are managed in Vercel Project Settings / `vercel env`.

## Prerequisites

- Python runtime available
- MongoDB available and reachable
- Supabase auth endpoint reachable
- Environment variables configured

## Local boot sequence

1. Create and activate virtual environment.
2. Install requirements.
3. Export required environment variables.
4. Start app.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BLOG_MONGODB_URL="mongodb+srv://<db_user>:<db_password>@<cluster-host>/blog_db?retryWrites=true&w=majority&appName=<app-name>"
export BLOG_MONGODB_DB_NAME="blog_db"
export SUPABASE_URL="https://<your-project-ref>.supabase.co"
export SUPABASE_JWT_AUDIENCE="authenticated"
export BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
uvicorn app.main:app --reload --port 3003
```

## Startup validation checklist

After start:

1. `GET /api/v1/blogs/ping` returns success.
2. `GET /api/v1/blogs/health` returns JSON with status fields.
3. Swagger UI is reachable at `/docs`.
4. One protected endpoint is tested with auth.

## Docker

The repository includes a `Dockerfile` that starts Uvicorn for `app.main:app`.
If building locally:

```bash
docker build -t chapters-blogs-backend .
docker run --rm -p 3003:3003 \
  -e BLOG_MONGODB_URL="mongodb://host.docker.internal:27017" \
  -e BLOG_MONGODB_DB_NAME="blog_db" \
  -e SUPABASE_URL="https://<your-project-ref>.supabase.co" \
  -e SUPABASE_JWT_AUDIENCE="authenticated" \
  chapters-blogs-backend
```

## Systemd deployment example

Use an application user and environment file in production (avoid embedding secrets in unit file).

Example commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-blogs-be
sudo systemctl start ai-blogs-be
sudo systemctl status ai-blogs-be
```

## Release and rollback sequence

Recommended release steps:

1. Pull new revision.
2. Install dependencies into venv.
3. Restart service.
4. Run smoke checks (`ping`, `health`, one read, one protected route).
5. Verify logs for startup and request errors.

Rollback steps:

1. Switch to previous known-good revision.
2. Reinstall dependencies if needed.
3. Restart service.
4. Re-run smoke checks.

## Vercel deployment flow

### One-time setup

```bash
vercel login
vercel link --yes
```

### Configure production env vars

Set in Vercel (recommended):

- `BLOG_MONGODB_URL`
- `BLOG_MONGODB_DB_NAME`
- `SUPABASE_URL`
- `SUPABASE_JWT_AUDIENCE`
- `BACKEND_CORS_ORIGINS` (JSON array string)
- `ENVIRONMENT`
- `DEBUG`
- `DEBUG_ENDPOINTS_ENABLED`

Example CORS value:

```bash
["http://localhost:3000","https://chapters-frontend-black.vercel.app","https://chapters-frontend.vercel.app"]
```

If local frontend calls deployed backend, localhost must be present in `BACKEND_CORS_ORIGINS` on Vercel.

### Deploy

```bash
vercel deploy --prod --yes
```

## Production hardening checklist

- Disable debug endpoints by config/policy.
- Restrict CORS to trusted frontend origins only.
- Enable stricter JWT checks (including audience).
- Ensure DB and Supabase auth settings come from secret/config store.

## Operational endpoints

- Health: `/api/v1/blogs/health`
- OpenAPI docs: `/docs`
- OpenAPI JSON: `/api/v1/blogs/openapi.json`

For incident response and troubleshooting, see [`OPERATIONS.md`](OPERATIONS.md).
