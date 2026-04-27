# Operations Runbook

## Service identity

- Service: Chapters Blogs Backend
- API root: `/api/v1/blogs`
- Primary dependencies: MongoDB, Supabase Auth

## Health and diagnostics

Primary endpoints:

- `GET /api/v1/blogs/ping`
- `GET /api/v1/blogs/health`
- `GET /docs`

Optional debug endpoints (disable in production):

- `/api/v1/blogs/debug/*`

## On-call quick triage

1. Check service process/container status.
2. Check app logs for startup/runtime exceptions.
3. Check `GET /health` response body:
   - auth provider status
   - database status
   - overall status
4. Validate MongoDB connectivity.
5. Validate Supabase JWKS endpoint reachability.

## Common incident patterns

### Symptom: protected routes return 401

Checks:

- caller sends Bearer token (for direct calls)
- Supabase URL and JWT audience settings are correct

### Symptom: blog read/write failures

Checks:

- `BLOG_MONGODB_URL` and `BLOG_MONGODB_DB_NAME`
- MongoDB service health and auth
- collection-level permissions
- frontend origin is included in `BACKEND_CORS_ORIGINS` (for browser requests)

### Symptom: health endpoint indicates degraded/unhealthy

Checks:

- Supabase auth provider availability
- MongoDB ping and count operation viability
- recent deploy/config drift

## Deployment verification checklist

After each deploy:

1. `ping` works.
2. `health` payload is well-formed.
3. one public read route works.
4. one authenticated write route works.
5. logs remain stable for several minutes.

## Vercel-specific checks

- Confirm latest production deployment is `READY`.
- Confirm backend alias resolves: `https://chapters-blogs-backend.vercel.app`.
- Verify Vercel env vars are present (especially `BLOG_MONGODB_URL`, `SUPABASE_URL`, `BACKEND_CORS_ORIGINS`).
- For local frontend testing (`http://localhost:3000` -> deployed backend), verify `BACKEND_CORS_ORIGINS` includes `http://localhost:3000`.
- For each new frontend Vercel alias/domain, verify it is explicitly added to `BACKEND_CORS_ORIGINS`.
- If runtime errors occur, inspect function logs using `vercel logs --environment production`.

## Rollback checklist

1. Revert to previous known-good revision/image.
2. Restart service.
3. Re-run smoke checks.
4. Confirm health and key business path behavior.

## Logging and observability suggestions

Current code uses print-heavy exception logging in places.
Recommended improvements:

- structured logging with request IDs
- centralized error/event logs
- request latency and dependency metrics
- auth failure and permission-denied trend dashboards

## Production guardrails

- debug routes disabled by policy
- strict CORS origin allowlist
- Vercel project env vars managed as encrypted values
- secret management for DB/Supabase credentials
- regular dependency and vulnerability review
