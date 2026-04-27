# Testing Guide

## Testing scope

This service currently has limited automated test coverage.
Testing should combine:

- API-level manual verification
- smoke checks after deploy
- targeted automated tests for critical risk paths

## Local prerequisites

- Service running on `http://localhost:3003`
- MongoDB Atlas and Supabase available
- A valid Supabase access token for protected route tests

## Fast smoke test checklist

1. `GET /api/v1/blogs/ping` returns success.
2. `GET /api/v1/blogs/public/blogs` returns list or expected not-found error.
3. Acquire Supabase token and call one protected endpoint.
4. `GET /api/v1/blogs/health` returns structured health payload.

## Manual API tests

### Obtain token

Use your frontend Supabase sign-in flow and copy the returned access token.

### Protected endpoint test

```bash
curl -X POST "http://localhost:3003/api/v1/blogs/createblog" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"comment_constraint":true,"tags":["qa"],"title":"Test","content":"Body"}'
```

### Comment/reply threading test

- Create blog
- Create comment on blog
- Create reply to comment
- Create nested reply to reply
- Fetch `GET /public/blog/{id}/comments` and verify nesting

### Ownership/authorization test

- User A creates content
- User B attempts update/delete
- Expect `403` from protected mutation route

## Existing test artifact

The repository includes `tests/test_auth.py`, which is a manual script-style checker for Bearer-only auth behavior rather than a full `pytest` suite.

## Recommended automated test priorities

1. Bearer token failure behavior in `get_current_user_id`.
2. Blog deletion cascade (blog/comments/replies consistency).
3. Health endpoint status-code behavior.
4. Reply recursion limits/edge behavior.
5. Like/unlike idempotency and count consistency.

## CI guidance

Until a full suite exists, CI should at least run:

- static checks/lint (if configured)
- import sanity check
- a small API smoke stage against ephemeral dependencies (Mongo + Supabase test project)

## Production smoke test (Vercel)

```bash
curl -i https://chapters-blogs-backend.vercel.app/api/v1/blogs/ping
curl -i https://chapters-blogs-backend.vercel.app/api/v1/blogs/health
curl -i https://chapters-blogs-backend.vercel.app/api/v1/blogs/public/blogs
```

### CORS verification (local frontend to deployed backend)

```bash
curl -i -X OPTIONS "https://chapters-blogs-backend.vercel.app/api/v1/blogs/public/blogs" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

Expected:
- `200 OK`
- `access-control-allow-origin: http://localhost:3000`
