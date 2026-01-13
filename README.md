# AI Portal Blog API

Blog API developed for the AI website "Chapter".

A modern blog API built with FastAPI, MongoDB, Keycloak authentication, and served through an Nginx gateway.

## Architecture Overview

```
Frontend → Nginx Gateway → Auth Service (Keycloak) → Blog API (FastAPI) → MongoDB
```

The blog API is part of a microservices architecture:
- **Nginx**: API gateway (port 443) - handles routing, SSL, and authentication proxy
- **Keycloak**: User management and authentication (port 8080)
- **Auth Service**: Node.js service for JWT validation (port 3002)
- **Blog API**: FastAPI service (port 3003)
- **MongoDB**: Database for blog posts, comments, and likes

## Project Structure

```plaintext
app/
├── api/                    # API endpoints
│   └── v1/
│       ├── api.py         # API router
│       └── endpoints/
│           └── blogs.py   # Blog endpoints
├── core/                  # Core application code
│   ├── __init__.py
│   ├── security.py       # Security utilities (Authentication)
│   ├── exceptions.py     # Custom exception classes for HTTP exceptions
│   ├── service_tracker.py       # Service tracking utilities
│   └── config.py         # Application configuration
├── db/                    # Database
│   ├── __init__.py
│   └── database.py       # MongoDB connection
├── schemas/              # Pydantic models
│   ├── __init__.py
│   ├── responses.py     # HTTP responses for swagger docs
│   └── blog.py          # Blog schemas
├── services/            # Business logic
│   ├── __init__.py
│   ├── keycloak.py      # Keycloak integration
│   └── blog.py         # Blog services
├── __init__.py         # App initialization
└── main.py             # FastAPI application
```

## Setup (for local development)

### Prerequisites

- Python 3.8+
- MongoDB instance running
- Keycloak server running
- Node.js (for auth-service, if testing locally)

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Keycloak Configuration
export KEYCLOAK_URL=https://aistudentchapter.lk/keycloak  # or http://localhost:8080
export KEYCLOAK_REALM=master
export BLOG_CLIENT_SECRET=your_keycloak_client_secret_here

# MongoDB Configuration
export BLOG_MONGODB_URL=mongodb://localhost:27017  # or your MongoDB connection string
export BLOG_MONGODB_DB_NAME=blog_db

# Optional: CORS origins (defaults are set in config.py)
# export BACKEND_CORS_ORIGINS=https://yourfrontend.com,http://localhost:3000
```

**Windows PowerShell:**
```powershell
$env:KEYCLOAK_URL="https://aistudentchapter.lk/keycloak"
$env:KEYCLOAK_REALM="master"
$env:BLOG_CLIENT_SECRET="your_secret"
$env:BLOG_MONGODB_URL="mongodb://localhost:27017"
$env:BLOG_MONGODB_DB_NAME="blog_db"
```

### 4. Run the application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 3003

# Production mode
uvicorn app.main:app --host 127.0.0.1 --port 3003
```

## Keycloak Configuration

The Blog API requires a properly configured Keycloak client for authentication.

### 1. Create a Keycloak Client

1. **Access Keycloak Admin Console**:
   - URL: `https://aistudentchapter.lk/keycloak/admin` (or `http://localhost:8080/admin`)
   - Login with admin credentials

2. **Create Client**:
   - Go to **Clients** → **Create client**
   - **Client ID**: `blogs-service`
   - **Client Protocol**: `openid-connect`
   - Click **Next**

3. **Configure Client Capabilities**:
   - **Client authentication**: `ON` (for confidential clients)
   - **Authorization**: `OFF`
   - **Standard flow**: `OFF` (optional, for browser flow)
   - **Direct access grants**: `ON` ⚠️ **FOR TESTING ONLY** (enables password grant for testing)
   - **Service accounts roles**: `ON` **REQUIRED FOR PRODUCTION** (for service-to-service calls)
   - Click **Next** → **Save**

4. **Get Client Secret**:
   - Go to **Credentials** tab
   - Copy the **Client Secret**
   - Set it as `BLOG_CLIENT_SECRET` environment variable

5. **Configure Client Scopes** (Optional):
   - Go to **Client scopes** tab
   - Add `blogs-service` to audience if needed
   - This fixes "Invalid audience" errors

### 2. Create Test Users

1. Go to **Users** → **Add user**
2. Set **Username**: `test-user`
3. **Email verified**: `ON` (optional)
4. **Enabled**: `ON` ⚠️ **REQUIRED**
5. Click **Create**

6. Set Password:
   - Go to **Credentials** tab
   - Click **Set password**
   - Enter password (e.g., `test`)
   - **Temporary**: `OFF` (so password doesn't expire)
   - Click **Save**

### 3. Verify Configuration

Test the setup using the debug endpoint:

```bash
# Get a token
curl -X POST "http://localhost:3003/api/v1/blogs/debug/get-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{"username": "test-user", "password": "test"}'

# If successful, you'll get an access_token
```

## Deploy as a service

To deploy the application as a service, you can use a process manager like `systemd` or `supervisord`. Here's a basic example using `systemd`:

1. Ensure the application is cloned to `/opt/`:

    Assume it is located at `/opt/ai-portal-blog-api/` after git clone.
    Follow the step 1 and step 2 of the Setup(local development) section above first.

2. Create a service file:

    ```bash
    sudo nano /etc/systemd/system/ai-blogs-be.service
    ```

3. Add the following configuration:

    ```ini
    [Unit]
    Description=AI Blog Service
    After=network.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/opt/ai-portal-blog-api
    ExecStart=/opt/ai-portal-blog-api/venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 3003
    Environment=BLOG_MONGODB_URL=your_db_connection_string_with_creds_here
    Environment=BLOG_CLIENT_SECRET=your_client_secret_here
    Environment=BLOG_MONGODB_DB_NAME=your_database_name_here
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

4. Start and enable the service:

    ```bash
    sudo systemctl start ai-blogs-be
    sudo systemctl enable ai-blogs-be
    ```

5. Restart the service:

    ```bash
    sudo systemctl restart ai-blogs-be
    ```

6. Stop the service:

    ```bash
    sudo systemctl stop ai-blogs-be
    ```

7. View logs:

    ```bash
    sudo journalctl -u ai-blogs-be
    ```

8. View service status

    ```bash
    sudo systemctl status ai-blogs-be
    ```

9. View all running services

    ```bash
    sudo systemctl list-units --type=service --state=running
    ```

## Nginx Configuration

The Blog API is served through an Nginx gateway that handles SSL, routing, and authentication.

### Location in Repository

The example Nginx configuration is located at:
```
nginx/aistudentchapter
```

### Key Configuration Points

1. **Authentication Proxy** (`/auth/validate`):
   - Nginx calls the auth service to validate Bearer tokens
   - Auth service verifies JWT against Keycloak
   - On success, sets `X-User-ID`, `X-User-Name`, `X-User-Role` headers

2. **Blog API Routes**:
   - **Public routes**: `/api/v1/blogs/public/*` (no auth required)
   - **Authenticated routes**: `/api/v1/blogs/*` (requires Bearer token)
   - **Debug routes**: `/api/v1/blogs/debug/*` (for development only)

3. **CORS Headers**:
   - Configured to allow frontend domain
   - Exposes custom headers (`X-User-ID`, etc.)

### Deploying Nginx Config

1. **Copy config to Nginx**:
   ```bash
   sudo cp nginx/aistudentchapter /etc/nginx/sites-available/aistudentchapter
   sudo ln -s /etc/nginx/sites-available/aistudentchapter /etc/nginx/sites-enabled/
   ```

2. **Test configuration**:
   ```bash
   sudo nginx -t
   ```

3. **Reload Nginx**:
   ```bash
   sudo systemctl reload nginx
   ```

### Important Nginx Directives

```nginx
location /api/v1/blogs/ {
    # Validate Bearer token via auth service
    auth_request /auth/validate;
    
    # Extract user info from auth service response
    auth_request_set $user_id $upstream_http_x_user_id;
    auth_request_set $user_name $upstream_http_x_user_name;
    auth_request_set $user_role $upstream_http_x_user_role;

    # Forward to blog API
    proxy_pass http://localhost:3003/api/v1/blogs/;
    
    # Pass user info to blog API
    proxy_set_header X-User-Id $user_id;
    proxy_set_header X-User-Name $user_name;
    proxy_set_header X-User-Role $user_role;
    
    # CORS headers
    add_header Access-Control-Allow-Origin "$http_origin" always;
    add_header Access-Control-Expose-Headers "X-User-ID, X-User-Name, X-User-Role" always;
}
```

## Nginx 

Restart nginx after configuration changes:

1. Test the correctness of the config

    ```bash
    sudo nginx -t
    ```

2. Restart nginx (ensure the syntax is correct with prior step)

    ```bash
    sudo systemctl reload nginx
    ```

## API Documentation

Once the application is running, you can access:

- **Interactive API documentation (Swagger UI)**: `http://localhost:3003/api/v1/blogs/docs`
- **Alternative API documentation (ReDoc)**: `http://localhost:3003/api/v1/blogs/redoc`
- **OpenAPI JSON**: `http://localhost:3003/api/v1/blogs/openapi.json`

### Production URLs (via Gateway)

- **Swagger UI**: `https://aistudentchapter.lk/api/v1/blogs/docs/`
- **Health Check**: `https://aistudentchapter.lk/api/v1/blogs/health`

## Testing with Swagger UI

### Method 1: Using Debug Endpoint (Easiest)

1. **Get a Bearer Token**:
   - Go to Swagger UI
   - Find `POST /debug/get-bearer-token` under **Debug** section
   - Click "Try it out"
   - Enter Keycloak username and password:
     ```json
     {
       "username": "test-user",
       "password": "test"
     }
     ```
   - Click "Execute"
   - Copy the `access_token` from the response

2. **Authorize in Swagger**:
   - Click the 🔒 **Authorize** button (top right)
   - Paste the token in the **HTTPBearer** value field
   - Click "Authorize"
   - Click "Close"

3. **Test Endpoints**:
   - Try `GET /debug/test-auth-with-bearer` first to verify authentication
   - Then test authenticated endpoints like `POST /createblog`

### Method 2: Direct Keycloak Token (Production)

If you have a token from your frontend or Keycloak directly:

```bash
# Get token from Keycloak
curl -X POST "https://aistudentchapter.lk/keycloak/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=blogs-service&client_secret=YOUR_SECRET&username=test-user&password=test"
```

Then use the `access_token` in Swagger's Authorize dialog.

### Method 3: Testing via X-User-ID Header (Gateway Only)

When requests go through the Nginx gateway:
- The gateway validates the Bearer token
- Sets `X-User-ID` header automatically
- Blog API reads the header

⚠️ **Note**: X-User-ID only works when requests pass through the Nginx gateway. Direct API calls require Bearer tokens.

## API Endpoints Overview

### Public Endpoints (No Authentication)

- `GET /api/v1/blogs/ping` - Health check
- `GET /api/v1/blogs/health` - Comprehensive health check
- `GET /api/v1/blogs/public/blogs` - Get all blogs
- `GET /api/v1/blogs/public/blogsByTags` - Get blogs by tags
- `GET /api/v1/blogs/public/blog/{blog_id}` - Get blog by ID
- `GET /api/v1/blogs/public/blog/{id}/comments` - Get comments for a blog

### Authenticated Endpoints (Require Bearer Token)

- `POST /api/v1/blogs/createblog` - Create a new blog post
- `PUT /api/v1/blogs/updateblog/{id}` - Update a blog post
- `DELETE /api/v1/blogs/blogs/{id}` - Delete a blog post
- `POST /api/v1/blogs/write-comment` - Write a comment
- `POST /api/v1/blogs/reply-comment` - Reply to a comment
- `PUT /api/v1/blogs/edit-comment-reply/{id}` - Edit comment/reply
- `DELETE /api/v1/blogs/delete-comment-reply/{id}` - Delete comment/reply
- `POST /api/v1/blogs/blog/{blog_id}/like` - Like/unlike a blog
- `GET /api/v1/blogs/blog/{blog_id}/like-status` - Check like status

### Debug Endpoints (Development Only)

⚠️ **Disable in production!**

- `POST /debug/get-bearer-token` - Get Keycloak token with username/password
- `GET /debug/test-auth-with-bearer` - Test Bearer token authentication
- `GET /debug/headers` - Inspect request headers
- `GET /debug/auth-info` - Debug authentication flow
- `GET /debug/keycloak-users` - List all Keycloak users
- `GET /debug/keycloak-users/{user_id}` - Get user by ID

## Features

- ✅ **CRUD operations** for blog posts, comments, and replies
- ✅ **MongoDB integration** with Motor (async driver)
- ✅ **Keycloak authentication** with JWT validation
- ✅ **Nginx API Gateway** integration
- ✅ **CORS support** for frontend integration
- ✅ **Async operations** throughout
- ✅ **Pydantic data validation** and serialization
- ✅ **Type hints** for better IDE support
- ✅ **Modular structure** for maintainability
- ✅ **API versioning** (`/api/v1/blogs`)
- ✅ **OpenAPI documentation** (Swagger UI + ReDoc)
- ✅ **Health check endpoint** with service status
- ✅ **Debug endpoints** for development/testing
- ✅ **Like/Unlike functionality** for blog posts
- ✅ **User information** passed from gateway

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KEYCLOAK_URL` | No | `https://aistudentchapter.lk/keycloak` | Keycloak server URL |
| `KEYCLOAK_REALM` | No | `master` | Keycloak realm name |
| `BLOG_CLIENT_SECRET` | Yes | - | Client secret from Keycloak |
| `BLOG_MONGODB_URL` | Yes | `mongodb://localhost:27017` | MongoDB connection string |
| `BLOG_MONGODB_DB_NAME` | Yes | - | MongoDB database name |
| `BACKEND_CORS_ORIGINS` | No | See config.py | Comma-separated list of allowed origins |

## Security Considerations

### Production Checklist

- [ ] Disable debug endpoints (remove or gate with environment check)
- [ ] Enable audience verification in `security.py` (set `verify_aud: True`)
- [ ] Use HTTPS only (enforce in Nginx)
- [ ] Restrict CORS origins to actual frontend domain
- [ ] Set strong `BLOG_CLIENT_SECRET`
- [ ] Use MongoDB with authentication enabled
- [ ] Enable Keycloak security features (2FA, password policies)
- [ ] Monitor logs for suspicious activity
- [ ] Rate limit API endpoints in Nginx
- [ ] Keep dependencies updated (`pip list --outdated`)

### Authentication Flow

**Production (through Gateway)**:
```
1. Frontend sends request with Bearer token
2. Nginx calls /auth/validate (auth-service)
3. Auth-service validates JWT against Keycloak JWKS
4. If valid, auth-service returns user headers
5. Nginx adds X-User-ID, X-User-Name, X-User-Role headers
6. Blog API receives request with user headers
7. Blog API uses X-User-ID for authorization
```

**Development (direct to Blog API)**:
```
1. Get token from POST /debug/get-bearer-token
2. Send request with Authorization: Bearer <token>
3. Blog API validates token against Keycloak JWKS
4. Blog API extracts user_id from token
5. Blog API processes request
```

## Contributing

When adding new features:
1. Follow the existing project structure
2. Add type hints to all functions
3. Update schemas in `app/schemas/blog.py`
4. Add response models in `app/schemas/responses.py`
5. Update this README with new endpoints or configuration
6. Test with both Bearer token and X-User-ID flows

## License

This project is licensed under the Apache License 2.0 - see below for details.

```
Copyright 2026 AI Student Chapter

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## Contact

For issues or questions, contact the AI Student Chapter team.

## Troubleshooting

### Common Issues and Solutions

#### 1. "Invalid issuer" Error

**Error**: `Invalid issuer. Expected: X, Got: Y`

**Solution**:
- Update `KEYCLOAK_URL` environment variable to match the actual Keycloak URL
- In `app/core/config.py`, the default is `https://aistudentchapter.lk/keycloak`
- If running locally, set: `export KEYCLOAK_URL=http://localhost:8080`

#### 2. "Invalid audience" Error

**Error**: `Invalid audience. Expected: blogs-service, Got: account`

**Solution**:
- In Keycloak Admin Console → Clients → blogs-service
- Add audience mapper or configure client scopes
- For development, audience verification is disabled in `security.py`

#### 3. "unauthorized_client" Error

**Error**: `Invalid client or Invalid client credentials`

**Solutions**:
- Verify `BLOG_CLIENT_SECRET` matches the Keycloak client secret
- In Keycloak: Clients → blogs-service → Credentials tab
- Ensure "Direct Access Grants Enabled" is ON (Capability config tab)

#### 4. CORS Errors from Frontend

**Symptoms**: Blocked by CORS policy

**Solutions**:
- Add your frontend domain to `BACKEND_CORS_ORIGINS` in `config.py`
- Ensure Nginx has CORS headers configured (see nginx config)
- Verify the frontend sends credentials: `credentials: 'include'`

#### 5. 401 Unauthorized in Swagger

**Solutions**:
- Use `POST /debug/get-bearer-token` to get a valid token
- Click Authorize button and paste the token
- Ensure user exists and is enabled in Keycloak
- Check that the password is correct

#### 6. "Algorithm not supported" Error

**Solution**:
- Install cryptography: `pip install cryptography`
- PyJWT requires cryptography for RS256/PS256 algorithms

#### 7. MongoDB Connection Issues

**Symptoms**: Service starts but database operations fail

**Solutions**:
- Verify `BLOG_MONGODB_URL` is set correctly
- Ensure MongoDB is running: `sudo systemctl status mongod`
- Check connection string includes credentials if auth is enabled
- Test connection: `mongosh "mongodb://localhost:27017"`

#### 8. Health Check Shows "unhealthy"

**Check** `GET /api/v1/blogs/health` response:

- **Keycloak status**: Failed → Check `KEYCLOAK_URL` and `BLOG_CLIENT_SECRET`
- **MongoDB status**: Failed → Check `BLOG_MONGODB_URL` and MongoDB service
- **Overall status**: degraded → One service is down but API still works

### Debug Endpoints Usage

Enable debug endpoints only in development. They are controlled by `is_debug_endpoint_enabled()`.

To disable in production:
- Set environment variable or modify `app/services/status.py`
- Remove or comment out debug endpoints in `app/api/v1/endpoints/blogs.py`

### Logs and Monitoring

**View systemd service logs**:
```bash
sudo journalctl -u ai-blogs-be -f
```

**Check service status**:
```bash
sudo systemctl status ai-blogs-be
```

**Nginx access logs**:
```bash
sudo tail -f /var/log/nginx/access.log
```

**Nginx error logs**:
```bash
sudo tail -f /var/log/nginx/error.log
```


## Troubleshoot

**502 error - bad gateway**
Most probably `nginx` is fine but the BE might not been started or enabled (verify with `systemctl status ai-blogs-be`. Enable the service and start it.
```bash
systemctl enable ai-blogs-be
systemctl start ai-blogs-be
```
