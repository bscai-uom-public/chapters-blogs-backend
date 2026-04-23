# Chapters Blogs Backend API and Contracts

## Base URL

All paths in this file are relative to:

`/api/v1/blogs`

## Endpoint catalog

### Public routes

- `GET /ping`
- `GET /health`
- `GET /public/blogs`
- `GET /public/blogsByTags?tags=tag1&tags=tag2`
- `GET /public/blog/{blog_id}`
- `GET /public/blog/{id}/comments`

### Authenticated routes

- `POST /createblog`
- `PUT /updateblog/{id}`
- `DELETE /blogs/{id}`
- `POST /write-comment`
- `POST /reply-comment`
- `PUT /edit-comment-reply/{id}`
- `DELETE /delete-comment-reply/{id}`
- `POST /blog/{blog_id}/like`
- `GET /blog/{blog_id}/like-status`

### Debug routes (internal/dev)

- `GET /debug/headers`
- `GET /debug/auth-info`
- `GET /debug/system-info`
- `GET /debug/test-auth-with-bearer`
- `POST /debug/get-bearer-token`
- `GET /debug/keycloak-users`
- `GET /debug/keycloak-users/{user_id}`

## Authentication contract

Protected endpoints depend on `get_current_user_id`:

1. Use `X-User-ID` header if present.
2. Else decode `Authorization: Bearer <token>` via Keycloak JWKS.
3. If neither is available/valid, return `401`.

For security, `X-User-ID` should be accepted only behind a trusted gateway.

## Core request/response examples

### Create blog

`POST /createblog`

Request:

```json
{
  "comment_constraint": true,
  "tags": ["backend", "fastapi"],
  "title": "Service design notes",
  "content": "Long form content...",
  "post_image": "https://example.com/image.png"
}
```

Response (`201`):

```json
{
  "blog_id": "f0b6d7b8-9bfa-4ec9-b669-a4f8b77f1e34",
  "comment_constraint": true,
  "tags": ["backend", "fastapi"],
  "number_of_views": 0,
  "likes_count": 0,
  "title": "Service design notes",
  "content": "Long form content...",
  "postedAt": "2026-04-23T08:54:30.101Z",
  "post_image": "https://example.com/image.png",
  "user_id": "keycloak-user-id",
  "user_username": "janith",
  "user_image_url": "",
  "user_first_name": "Janith",
  "user_last_name": "..."
}
```

### Write comment

`POST /write-comment`

Request:

```json
{
  "blogPost_id": "f0b6d7b8-9bfa-4ec9-b669-a4f8b77f1e34",
  "text": "Great post."
}
```

Response (`201`) returns a `CommentBase` payload with nested `replies`.

### Like/unlike

`POST /blog/{blog_id}/like`

Request:

```json
{
  "like_value": 1
}
```

Response:

```json
{
  "message": "Blog liked successfully",
  "liked": true
}
```

`like_value` accepts only `0` (unlike) or `1` (like).

## Error contract

Common status codes returned across routes:

- `400`: invalid request values (for example invalid like value).
- `401`: auth missing/invalid token/header.
- `403`: ownership/permission violation on protected resources.
- `404`: entity not found (blog/comment/reply/user).
- `422`: schema validation failure from FastAPI/Pydantic.
- `500`: unexpected server-side failure.
- `503`: degraded or unhealthy service status from `/health` contract (documented; implementation has a known status-code propagation issue).

Typical error shape:

```json
{
  "detail": "Human-readable error message"
}
```

## Response modeling conventions

- IDs are stored as Mongo `_id` and serialized as logical IDs via schema aliases.
- Many read payloads include Keycloak-enriched user fields:
  - `user_username`
  - `user_image_url`
  - `user_first_name`
  - `user_last_name`

## Compatibility and versioning notes

- This is currently a v1 API with prefix `/api/v1/blogs`.
- Route renames or auth behavior changes must be treated as breaking changes.
- When introducing v2, keep v1 available during migration with explicit deprecation notice.
