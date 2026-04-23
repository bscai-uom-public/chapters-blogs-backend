# Chapters Blogs Backend

FastAPI backend for blog posts, comments, replies, and likes in the AI Portal ecosystem.

## What this service does

- Serves versioned REST APIs under `/api/v1/blogs`.
- Stores blog-domain data in MongoDB (`Blogs`, `Comments`, `Replies`, `Likes`).
- Uses Keycloak for user identity and profile enrichment.
- Supports two auth input modes:
  - trusted gateway header (`X-User-ID`)
  - direct Bearer token validation against Keycloak JWKS

## Architecture overview

```text
Client -> (Gateway or direct call) -> FastAPI router -> service layer -> MongoDB
                                                 -> Keycloak (token + user info)
```

Core request path:

1. Route handler in `app/api/v1/endpoints/blogs.py`
2. Auth dependency `get_current_user_id` in `app/core/security.py` (for protected routes)
3. Domain logic in `app/services/blog.py`
4. Persistence via collections from `app/db/database.py`
5. Response schemas from `app/schemas/blog.py`

## Project structure

```text
app/
  main.py                      # FastAPI app bootstrapping + CORS + OpenAPI path
  api/v1/api.py                # API v1 router composition
  api/v1/endpoints/blogs.py    # All health/blog/comment/like/debug endpoints
  core/config.py               # Runtime configuration
  core/security.py             # Auth dependency and Bearer token decoding
  core/exceptions.py           # Domain-specific HTTP exceptions
  core/service_tracker.py      # Uptime tracking used by health endpoint
  db/database.py               # Mongo client + collection handles
  schemas/blog.py              # Request/response models and health schemas
  schemas/responses.py         # OpenAPI response metadata
  services/blog.py             # Blog/comment/reply/like business logic
  services/keycloak.py         # Keycloak token and user queries
  services/status.py           # Health and debug support logic
docs/
  ARCHITECTURE.md
  API_AND_CONTRACTS.md
  DATA_MODELS_AND_STORAGE.md
  AUTH_README.md
  RUN_AND_DEPLOY.md
  CORS_AUTH_FIXES.md
```

## Quick start (local)

### Prerequisites

- Python 3.10+ (recommended)
- MongoDB reachable from this service
- Keycloak realm/client available

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
export KEYCLOAK_URL="http://localhost:8080"  # include /keycloak if your deployment uses that base path
export KEYCLOAK_REALM="master"
export BLOG_CLIENT_SECRET="your_client_secret"
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
| `KEYCLOAK_URL` | `app/core/config.py` | `https://aistudentchapter.lk/keycloak` | Yes | Keycloak base URL |
| `KEYCLOAK_REALM` | `app/core/config.py` | `master` | Yes | Keycloak realm |
| `BLOG_CLIENT_SECRET` | `app/core/config.py` | empty string | Yes | Keycloak confidential client secret |
| `ENVIRONMENT` | `app/services/status.py` | `development` | Recommended | Environment name used by debug gating |
| `DEBUG_ENDPOINTS_ENABLED` | `app/services/status.py` | `true` | Must set carefully | Additional debug endpoint gate |
| `DEBUG` | `app/services/status.py` | `false` | Optional | Debug flag in system-info output |
| `SERVICE_VERSION` | `app/services/status.py` | `unknown` | Recommended | Included in system-info output |

## API endpoint groups

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
- `GET /api/v1/blogs/debug/keycloak-users`
- `GET /api/v1/blogs/debug/keycloak-users/{user_id}`

## Auth behavior

Protected routes use `get_current_user_id` with this precedence:

1. `X-User-ID` header if present.
2. Bearer token (`Authorization: Bearer ...`) decoded and verified via Keycloak JWKS.

Important security note:

- Trusting `X-User-ID` is only safe behind a trusted gateway that injects it.
- Direct exposure of this service without gateway hardening can allow header spoofing.

See [`docs/AUTH_README.md`](docs/AUTH_README.md) for full details and examples.

## Deployment notes

For runbook-grade deploy/rollback steps, see:

- [`docs/RUN_AND_DEPLOY.md`](docs/RUN_AND_DEPLOY.md)
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)

## Security hardening checklist

- Disable or remove debug endpoints in non-dev environments.
- Enforce strict gateway controls if `X-User-ID` is accepted.
- Enable audience validation in Bearer token verification (`verify_aud`).
- Restrict CORS origins to known frontends only.
- Use secret management for `BLOG_CLIENT_SECRET` and DB credentials.

## Documentation index

See [`docs/README.md`](docs/README.md) for the full docs map.
