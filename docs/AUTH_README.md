# Authentication and Authorization

## Current behavior summary

Protected routes in this service depend on `get_current_user_id` from `app/core/security.py`.
Identity is resolved from a Supabase Bearer token only:

1. Read `Authorization: Bearer <token>`.
2. Resolve signing key from `${SUPABASE_URL}/auth/v1/.well-known/jwks.json`.
3. Validate signature, issuer, expiration, and optional audience (`SUPABASE_JWT_AUDIENCE`).
4. Extract user ID from `sub`.

If token validation fails, the route returns `401`.

## Route scope

All paths in this document are under `/api/v1/blogs`.

### Protected routes

- `POST /createblog`
- `PUT /updateblog/{id}`
- `DELETE /blogs/{id}`
- `POST /write-comment`
- `POST /reply-comment`
- `PUT /edit-comment-reply/{id}`
- `DELETE /delete-comment-reply/{id}`
- `POST /blog/{blog_id}/like`
- `GET /blog/{blog_id}/like-status`
- Some debug routes, such as `GET /debug/auth-info` and `GET /debug/test-auth-with-bearer`

### Public routes

- `GET /ping`
- `GET /health`
- `GET /public/blogs`
- `GET /public/blogsByTags`
- `GET /public/blog/{blog_id}`
- `GET /public/blog/{id}/comments`

## Bearer token flow (direct calls)

1. Client sends `Authorization: Bearer <token>`.
2. Service loads JWKS from:
   - `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
3. Token is decoded and validated.
4. User ID is extracted from `sub` (fallback: `preferred_username`).

Example:

```bash
curl -X POST "http://localhost:3003/api/v1/blogs/createblog" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"comment_constraint": true, "tags": ["dev"], "title": "T", "content": "Body"}'
```

## Common auth errors

`401 Unauthorized` examples:

- missing `Authorization` header
- invalid token format/signature/issuer
- expired token

Typical shape:

```json
{
  "detail": "User authentication required. Provide a valid Bearer token."
}
```

`403 Forbidden` examples:

- user attempts to update/delete content owned by another user

## Security considerations

- Debug endpoints include auth and user-info helpers; they should be disabled for production.
- Keep `SUPABASE_URL` and `SUPABASE_JWT_AUDIENCE` aligned with your Supabase project settings.
- Ensure production CORS config (`BACKEND_CORS_ORIGINS`) allows your deployed frontend origins.

See [`CURRENT_ISSUES.md`](CURRENT_ISSUES.md) for remediation priorities.
