# CORS and Authentication Fixes - Implementation Summary

## Overview
Three critical issues have been fixed to enable proper frontend integration and Swagger UI testing:
1. **CORS Error on createBlog endpoint**
2. **Swagger UI authentication testing**
3. **401 errors when providing X-User-ID**

---

## Issue 1: CORS Fix ✅

### Changes Made:

#### 1. Updated `app/core/config.py`
- Added your production domain to `BACKEND_CORS_ORIGINS`:
  ```python
  BACKEND_CORS_ORIGINS: List[str] = [
      "*",  # Wildcard for development
      "http://localhost:3000",
      "https://localhost:3000",
      "https://aistudentchapter.lk",        # ← Added
      "https://www.aistudentchapter.lk",    # ← Added
      "http://localhost",                    # ← Added
  ]
  ```

#### 2. Updated `app/main.py`
- Added `expose_headers=["*"]` to CORS middleware:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
      expose_headers=["*"],  # ← NEW: Exposes X-User-ID, X-User-Role, etc.
  )
  ```

#### 3. Updated `nginx/aistudentchapter`
- Added CORS headers to the `/api/v1/blogs/` location block:
  ```nginx
  # CORS headers to allow frontend to access responses
  add_header Access-Control-Allow-Origin "$http_origin" always;
  add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
  add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-User-ID, X-User-Name, X-User-Role" always;
  add_header Access-Control-Expose-Headers "X-User-ID, X-User-Name, X-User-Role" always;
  add_header Access-Control-Allow-Credentials "true" always;
  ```

### How It Fixes CORS:
- **Frontend requests** from `aistudentchapter.lk` are now explicitly allowed
- **Preflight (OPTIONS) requests** for POST methods are properly handled
- **Custom headers** like `X-User-ID` are exposed to the frontend
- **Credentials** (cookies/auth) are allowed in cross-origin requests

### Testing:
```bash
# Frontend should now be able to call POST /api/v1/blogs/createblog without CORS errors
```

---

## Issue 2: Swagger UI Authentication ✅

### Changes Made:

#### 1. Updated `app/core/security.py` (Complete Rewrite)

**New imports:**
```python
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials
import jwt
import httpx
```

**New function: `decode_token_from_bearer()`**
- Accepts Bearer tokens from Authorization header
- Validates tokens against Keycloak's JWKS (public keys)
- Extracts user_id from the token's `sub` claim
- Handles token expiration and invalid tokens

**Updated function: `get_current_user_id()`**
- Now accepts **both** Bearer tokens AND X-User-ID headers
- Priority:
  1. **X-User-ID header** (from nginx gateway after validation)
  2. **Bearer token** (for direct API calls and Swagger testing)
- Provides clear error message if neither is provided

### How It Works for Swagger Testing:

**Step 1: Get a Keycloak Token**
```bash
curl -X POST "https://aistudentchapter.lk/keycloak/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=blogs-service&username=testuser&password=testpass"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  ...
}
```

**Step 2: Copy the `access_token` value**

**Step 3: Use in Swagger UI**
1. Open Swagger UI: `https://aistudentchapter.lk/api/v1/blogs/docs/`
2. Click the 🔒 **Authorize** button (top right)
3. Select `HTTPBearer` scheme
4. Paste the token in the "value" field
5. Click "Authorize"
6. Now test authenticated endpoints like `POST /createblog`

#### 2. Added Debug Endpoint in `app/api/v1/endpoints/blogs.py`

New endpoint: `GET /debug/test-auth-with-bearer`
- Tests Bearer token authentication
- Provides instructions for Swagger testing
- Returns user_id to confirm authentication worked
- Tag: `[Debug]`

```python
@router.get("/debug/test-auth-with-bearer", tags=["Debug"])
async def test_auth_with_bearer(current_user_id: str = Depends(get_current_user_id)):
    """
    Test endpoint for Bearer token authentication in Swagger UI.
    Try this first to verify your token works!
    """
    return {
        "success": True,
        "user_id": current_user_id,
        "note": "Your Bearer token is valid"
    }
```

### How It Fixes Swagger Auth:
- Swagger can now send Bearer tokens in Authorization header
- Blog API validates tokens against Keycloak's public keys
- User is properly authenticated for testing
- Production flow (through gateway) still works unchanged
- **Development and production flows are now compatible**

---

## Issue 3: 401 Error with X-User-ID ✅

### Root Cause Analysis:
The nginx gateway uses `auth_request /auth/validate` which:
1. **Expects** a Bearer token in Authorization header
2. **Validates** the token via auth-service
3. **Returns** X-User-ID header if validation succeeds
4. **Rejects** requests without a Bearer token (even if X-User-ID is provided)

Flow:
```
Frontend Request with Bearer Token
       ↓
Nginx Gateway (port 443)
       ↓
auth_request /auth/validate (validates Bearer token)
       ↓
Auth Service (port 3002) - verifies token with Keycloak
       ↓
Returns X-User-ID header (if token is valid)
       ↓
Nginx forwards to Blog API with X-User-ID header (port 3003)
       ↓
Blog API receives X-User-ID and processes request
```

### The Fix:
Updated security.py to handle **both** scenarios:
1. **Production (Gateway):** Request has X-User-ID (from gateway validation) ✓
2. **Direct/Swagger:** Request has Bearer token (validated by blog API) ✓

### How It Works:
- **With Bearer token:** Blog API validates it and extracts user_id
- **With X-User-ID:** Blog API uses it directly (already validated by gateway)
- **Without either:** Returns 401 with clear error message

### For Frontend:
```javascript
// This is what the frontend should do:
fetch('https://aistudentchapter.lk/api/v1/blogs/createblog', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${keycloakToken}`,  // ← This is essential
    'Content-Type': 'application/json'
  },
  credentials: 'include',  // Include CORS cookies
  body: JSON.stringify(blogData)
})
```

---

## Summary of Files Changed

| File | Change | Reason |
|------|--------|--------|
| `app/core/config.py` | Added production domains | CORS: Whitelist FE domains |
| `app/main.py` | Added `expose_headers=["*"]` | CORS: Allow FE to read response headers |
| `app/core/security.py` | Complete rewrite | Auth: Support Bearer tokens + X-User-ID |
| `app/api/v1/endpoints/blogs.py` | Added test endpoint | Testing: Debug Bearer token validation |
| `nginx/aistudentchapter` | Added CORS headers | CORS: Gateway-level header handling |

---

## Testing Checklist

### ✅ Test CORS Fix
```bash
# From frontend (different domain)
curl -X POST 'https://aistudentchapter.lk/api/v1/blogs/createblog' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test","content":"Content","tags":[]}'

# Should NOT get CORS error
```

### ✅ Test Swagger Authentication
1. Get token from Keycloak
2. Click Authorize in Swagger
3. Enter `<token_value>` in HTTPBearer field
4. Try GET `/debug/test-auth-with-bearer` - should return your user_id
5. Try POST `/createblog` - should work with your user_id

### ✅ Test X-User-ID Flow (Production)
- Requests through nginx gateway should include Bearer token
- Gateway validates and adds X-User-ID header
- Blog API receives both Bearer token AND X-User-ID
- Request succeeds with either (prefers X-User-ID from gateway)

### ✅ Test Direct API Calls
```bash
# Test with Bearer token (Swagger or direct API)
curl -X GET 'http://localhost:3003/api/v1/blogs/debug/test-auth-with-bearer' \
  -H 'Authorization: Bearer <token>'

# Should return: {"success": true, "user_id": "...", "note": "..."}
```

---

## Production Deployment Notes

### Security Considerations:
1. **Remove or disable debug endpoints** in production:
   - `/debug/test-auth-with-bearer`
   - `/debug/headers`
   - `/debug/auth-info`
   - `/debug/system-info`
   - `/debug/keycloak-users*`

2. **CORS Wildcard (`"*"`)**: Keep for development, restrict in production:
   ```python
   # Production:
   BACKEND_CORS_ORIGINS: List[str] = [
       "https://aistudentchapter.lk",
       "https://www.aistudentchapter.lk",
   ]
   ```

3. **Token Validation**: Blog API now validates Bearer tokens directly. Ensure Keycloak is accessible and properly configured.

4. **Nginx Gateway**: Still validates tokens, providing defense in depth.

### Environment Variables Needed:
- `KEYCLOAK_URL` - Keycloak server URL
- `KEYCLOAK_REALM` - Keycloak realm (default: "master")
- `BLOG_CLIENT_SECRET` - Client secret for blogs-service

---

## Additional Resources

### Keycloak Token Generation:
```bash
KEYCLOAK_URL="https://aistudentchapter.lk/keycloak"
REALM="master"
CLIENT_ID="blogs-service"

# Password grant flow (for testing)
curl -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=$CLIENT_ID&username=testuser&password=testpass"
```

### JWT Token Structure:
The token contains claims like:
- `sub` - User ID (extracted for X-User-ID)
- `preferred_username` - Username
- `email` - Email
- `realm_access.roles` - User roles
- `exp` - Expiration time

---

## Questions or Issues?

If you encounter any problems:
1. Check the **security.py** file for token validation errors
2. Verify Keycloak connectivity: `GET /auth/public-key-info`
3. Test Bearer token decoding: `POST /auth/debug-token` (auth-service endpoint)
4. Check nginx gateway logs: `sudo docker logs <nginx-container>`
5. Verify CORS headers: Check browser's Network tab → Response Headers

