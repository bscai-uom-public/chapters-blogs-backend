from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from jwt import PyJWKClient
from app.core.config import settings

security = HTTPBearer(description="Bearer token from Keycloak", auto_error=False)


async def decode_token_from_bearer(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Decode a Bearer token to extract the user_id using Keycloak JWKS via PyJWKClient.
    """
    try:
        token = credentials.credentials

        # Inspect token header to determine algorithm
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")

        # Resolve signing key from JWKS
        jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.REALM}/protocol/openid-connect/certs"
        jwks_client = PyJWKClient(jwks_url)
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Unable to resolve signing key: {str(e)}")

        # Verify and decode the token using the resolved key and the actual algorithm
        try:
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg] if alg else ["RS256"],
                audience=settings.CLIENT_ID,
                issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.REALM}"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        # Extract user_id from token (prefer 'sub' which is the user ID in Keycloak)
        user_id = decoded.get("sub") or decoded.get("preferred_username")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        return user_id

    except HTTPException:
        raise
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
