from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from jwt import PyJWKClient
from app.core.config import settings
from app.services.auth_provider import cache_user_profile_from_claims

security = HTTPBearer(description="Bearer token from Supabase Auth", auto_error=False)


async def decode_token_from_bearer(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Decode a Supabase Bearer token and extract user_id.
    """
    try:
        token = credentials.credentials

        # Decode without verification first to inspect claims
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")

        if not settings.SUPABASE_URL:
            raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured.")

        # Resolve signing key from Supabase JWKS
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Unable to resolve signing key: {str(e)}")

        # Expected values
        expected_issuer = f"{settings.SUPABASE_URL}/auth/v1"
        expected_audience = settings.SUPABASE_JWT_AUDIENCE

        # Verify and decode the token using the resolved key and the actual algorithm
        try:
            verify_audience = bool(expected_audience)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg] if alg else ["RS256"],
                issuer=expected_issuer,
                audience=expected_audience if verify_audience else None,
                options={"verify_aud": verify_audience}
            )
        except jwt.InvalidIssuerError as e:
            # Show what issuer we got vs what we expected
            actual_issuer = unverified.get("iss")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid issuer. Expected: {expected_issuer}, Got: {actual_issuer}"
            )
        except jwt.InvalidAudienceError as e:
            actual_audience = unverified.get("aud")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid audience. Expected: {expected_audience}, Got: {actual_audience}"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        # Extract user_id from token (prefer 'sub' as canonical user ID)
        user_id = decoded.get("sub") or decoded.get("preferred_username")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        cache_user_profile_from_claims(user_id, decoded)
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
    1. Bearer token (primary mode)
    2. X-User-ID header only when explicitly allowed via ALLOW_TRUSTED_X_USER_ID
    
    NOTE: X-User-ID can be accepted only when ALLOW_TRUSTED_X_USER_ID is enabled.
    For direct API calls and Swagger testing, provide a valid Supabase Bearer token.
    
    Bearer token format: Authorization: Bearer <supabase_access_token>
    """
    # Priority 1: Bearer token
    if credentials:
        return await decode_token_from_bearer(credentials)

    # Transitional fallback for trusted gateway mode only.
    if settings.ALLOW_TRUSTED_X_USER_ID and x_user_id:
        return x_user_id

    raise HTTPException(
        status_code=401,
        detail="User authentication required. Provide a valid Bearer token."
    )
