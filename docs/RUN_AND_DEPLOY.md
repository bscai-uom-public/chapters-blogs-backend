# Chapters Blogs Backend Run and Deploy

## Runtime profiles

### Profile A: local direct API

- Caller talks directly to FastAPI on port `3003`.
- Auth usually tested with Bearer token flow.
- Useful for local development and debugging.

### Profile B: gateway-backed production

- Gateway/Auth layer sits in front of this service.
- Recommended for production traffic isolation and policy enforcement.

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
export BLOG_MONGODB_URL="mongodb://localhost:27017"
export BLOG_MONGODB_DB_NAME="blog_db"
export SUPABASE_URL="https://<your-project-ref>.supabase.co"
export SUPABASE_JWT_AUDIENCE="authenticated"
uvicorn app.main:app --reload --port 3003
```

## Startup validation checklist

After start:

1. `GET /api/v1/blogs/ping` returns success.
2. `GET /api/v1/blogs/health` returns JSON with status fields.
3. Swagger UI is reachable at `/api/v1/blogs/docs`.
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

## Production hardening checklist

- Disable debug endpoints by config/policy.
- Restrict CORS to trusted frontend origins only.
- Enable stricter JWT checks (including audience).
- Ensure DB and Supabase auth settings come from secret/config store.

## Operational endpoints

- Health: `/api/v1/blogs/health`
- OpenAPI docs: `/api/v1/blogs/docs`
- OpenAPI JSON: `/api/v1/blogs/openapi.json`

For incident response and troubleshooting, see [`OPERATIONS.md`](OPERATIONS.md).
