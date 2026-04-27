# Chapters Blogs Backend

FastAPI backend for blog posts, comments, replies, and likes in the AI Portal ecosystem.

## What this service does

- Serves REST APIs under `/api/v1/blogs`.
- Stores blog-domain data in MongoDB (`Blogs`, `Comments`, `Replies`, `Likes`).
- Uses Supabase Auth JWT validation for protected routes.

## Authentication model

Protected routes require:

- `Authorization: Bearer <supabase_access_token>`

The backend validates tokens against Supabase JWKS and uses `sub` as the authenticated user ID.

## Quick start (local)

### Prerequisites

- Python 3.10+ (recommended)
- MongoDB reachable from this service
- Supabase project URL and valid access token flow from frontend

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Required environment variables

```bash
export BLOG_MONGODB_URL="mongodb://localhost:27017"
export BLOG_MONGODB_DB_NAME="blog_db"
export SUPABASE_URL="https://your-project-ref.supabase.co"
export SUPABASE_JWT_AUDIENCE="authenticated"
```

### Run

```bash
uvicorn app.main:app --reload --port 3003
```

API docs:

- Swagger: `http://localhost:3003/api/v1/blogs/docs`
- ReDoc: `http://localhost:3003/api/v1/blogs/redoc`
- OpenAPI JSON: `http://localhost:3003/api/v1/blogs/openapi.json`

## Environment variable reference

| Variable | Used in code | Default | Required in production | Purpose |
|---|---|---|---|---|
| `BLOG_MONGODB_URL` | `app/core/config.py` | `mongodb://localhost:27017` | Yes | MongoDB connection URI |
| `BLOG_MONGODB_DB_NAME` | `app/core/config.py` | empty string | Yes | MongoDB database name |
| `SUPABASE_URL` | `app/core/config.py` | empty string | Yes | Supabase project URL for issuer and JWKS |
| `SUPABASE_JWT_AUDIENCE` | `app/core/config.py` | `authenticated` | Recommended | Expected JWT audience |
| `BACKEND_CORS_ORIGINS` | `app/core/config.py` | local defaults | Yes | Allowed frontend origins |
| `ENVIRONMENT` | `app/services/status.py` | `development` | Recommended | Environment name used by debug gating |
| `DEBUG_ENDPOINTS_ENABLED` | `app/services/status.py` | `true` | Must set carefully | Additional debug endpoint gate |
| `DEBUG` | `app/services/status.py` | `false` | Optional | Debug flag in system-info output |
| `SERVICE_VERSION` | `app/services/status.py` | `unknown` | Recommended | Included in system-info output |

## Endpoint groups

Public:

- `GET /api/v1/blogs/ping`
- `GET /api/v1/blogs/health`
- `GET /api/v1/blogs/public/blogs`
- `GET /api/v1/blogs/public/blogsByTags?tags=...`
- `GET /api/v1/blogs/public/blog/{blog_id}`
- `GET /api/v1/blogs/public/blog/{id}/comments`

Authenticated:

- `POST /api/v1/blogs/createblog`
- `PUT /api/v1/blogs/updateblog/{id}`
- `DELETE /api/v1/blogs/blogs/{id}`
- `POST /api/v1/blogs/write-comment`
- `POST /api/v1/blogs/reply-comment`
- `PUT /api/v1/blogs/edit-comment-reply/{id}`
- `DELETE /api/v1/blogs/delete-comment-reply/{id}`
- `POST /api/v1/blogs/blog/{blog_id}/like`
- `GET /api/v1/blogs/blog/{blog_id}/like-status`

Debug/internal:

- `GET /api/v1/blogs/debug/headers`
- `GET /api/v1/blogs/debug/auth-info`
- `GET /api/v1/blogs/debug/system-info`
- `GET /api/v1/blogs/debug/test-auth-with-bearer`
- `POST /api/v1/blogs/debug/get-bearer-token`
- `GET /api/v1/blogs/debug/auth-users`
- `GET /api/v1/blogs/debug/auth-users/{user_id}`

## Documentation index

- `docs/AUTH_README.md`
- `docs/ARCHITECTURE.md`
- `docs/API_AND_CONTRACTS.md`
- `docs/OPERATIONS.md`
- `docs/TESTING.md`
