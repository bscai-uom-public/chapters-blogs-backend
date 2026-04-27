# Authentication and Authorization

## Current behavior summary

Protected routes in this service depend on `get_current_user_id` from `app/core/security.py`.
Identity is resolved in this order:

1. `X-User-ID` header (if present)
2. Bearer token from `Authorization` header (decoded against Keycloak JWKS)

If neither path succeeds, the route returns `401`.

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
   - `{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs`
3. Token is decoded and validated.
4. User ID is extracted from `sub` (fallback: `preferred_username`).

Example:

```bash
curl -X POST "http://localhost:3003/api/v1/blogs/createblog" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"comment_constraint": true, "tags": ["dev"], "title": "T", "content": "Body"}'
```

## Gateway header flow (`X-User-ID`)

When traffic is routed through a trusted gateway:

1. Gateway validates JWT upstream.
2. Gateway injects `X-User-ID`.
3. Service uses header directly for ownership enforcement.

Important:

- Direct clients must not be able to set this header unchecked.
- If this backend is reachable directly from the internet, this trust model is unsafe.

## Common auth errors

`401 Unauthorized` examples:

- missing auth header and missing `X-User-ID`
- invalid token format/signature/issuer
- expired token

Typical shape:

```json
{
  "detail": "User authentication required. Provide either: (1) Bearer token in Authorization header, or (2) X-User-ID header."
}
```

`403 Forbidden` examples:

- user attempts to update/delete content owned by another user

## Security considerations

- `verify_aud` is currently disabled in token decoding logic, which weakens token audience checks.
- Debug endpoints include auth and user-info helpers; they should be disabled for production.
- `X-User-ID` precedence over Bearer token means upstream trust boundary must be enforced carefully.

See [`CURRENT_ISSUES.md`](CURRENT_ISSUES.md) for remediation priorities.
