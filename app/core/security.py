from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import httpx
from app.core.config import settings

security = HTTPBearer(description="Bearer token from Keycloak", auto_error=False)


async def decode_token_from_bearer(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Decode a Bearer token to extract the user_id.
    For testing/Swagger purposes, this accepts tokens from Keycloak.
    In production, the nginx gateway handles this.
    """
    try:
        token = credentials.credentials
        
        # Fetch JWKS from Keycloak to verify the token
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(
                f"{settings.KEYCLOAK_URL}/realms/{settings.REALM}/protocol/openid-connect/certs",
                timeout=10
            )
            if jwks_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to fetch Keycloak JWKS")
            
            jwks = jwks_response.json()
        
        # Decode without verification first to get the header
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the key matching the kid in the token header
        matching_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                matching_key = key
                break
        
        if not matching_key:
            raise HTTPException(status_code=401, detail="Token key not found")
        
        # Construct the public key from the certificate
        public_key = f"-----BEGIN CERTIFICATE-----\n{matching_key['x5c'][0]}\n-----END CERTIFICATE-----"
        
        # Verify and decode the token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.CLIENT_ID,
            issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.REALM}"
        )
        
        # Extract user_id from token (prefer 'sub' which is the user ID in Keycloak)
        user_id = decoded.get("sub") or decoded.get("preferred_username")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None)
) -> str:
    """
    Extract user_id from request in this priority order:
    1. X-User-ID header (set by nginx gateway after token validation)
    2. Bearer token (for direct API calls and Swagger testing)
    
    NOTE: X-User-ID is set by the nginx gateway after it validates the Bearer token.
    When testing via Swagger, you must provide a valid Bearer token from Keycloak.
    
    Bearer token format: Authorization: Bearer <token_from_keycloak>
    """
    # Priority 1: Check for X-User-ID header (from gateway)
    if x_user_id:
        return x_user_id
    
    # Priority 2: Check for Bearer token (for direct calls and Swagger)
    if credentials:
        return await decode_token_from_bearer(credentials)
    
    # Neither header nor token provided
    raise HTTPException(
        status_code=401,
        detail="User authentication required. Provide either: (1) Bearer token in Authorization header, or (2) X-User-ID header."
    )
