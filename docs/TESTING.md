# Testing Guide

## Testing scope

This service currently has limited automated test coverage.
Testing should combine:

- API-level manual verification
- smoke checks after deploy
- targeted automated tests for critical risk paths

## Local prerequisites

- Service running on `http://localhost:3003`
- MongoDB and Keycloak available
- A valid user in Keycloak for protected route tests

## Fast smoke test checklist

1. `GET /api/v1/blogs/ping` returns success.
2. `GET /api/v1/blogs/public/blogs` returns list or expected not-found error.
3. Acquire token and call one protected endpoint.
4. `GET /api/v1/blogs/health` returns structured health payload.

## Manual API tests

### Obtain token (debug helper)

```bash
curl -X POST "http://localhost:3003/api/v1/blogs/debug/get-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{"username":"test-user","password":"test-password"}'
```

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

The repository includes `tests/test_auth.py`, which is a manual script-style checker rather than a full `pytest` suite.

## Recommended automated test priorities

1. Auth precedence and failure behavior in `get_current_user_id`.
2. Blog deletion cascade (blog/comments/replies consistency).
3. Health endpoint status-code behavior.
4. Reply recursion limits/edge behavior.
5. Like/unlike idempotency and count consistency.

## CI guidance

Until a full suite exists, CI should at least run:

- static checks/lint (if configured)
- import sanity check
- a small API smoke stage against ephemeral dependencies (Mongo + Keycloak mocks or test realm)
