"""
Authentication & role resolution for the blogs backend.

Bearer-token only — the previous X-User-ID fallback has been removed because
it allowed trivial spoofing. Roles are derived from the email claim on the
Supabase JWT: an email in ``settings.ADMIN_EMAILS`` is an admin, otherwise
the caller is a student.
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from jwt import PyJWKClient

from app.core.config import settings
from app.services.auth_provider import cache_user_profile_from_claims


security = HTTPBearer(description="Bearer token from Supabase Auth", auto_error=False)


def _decode_bearer(token: str) -> dict:
    """Decode and verify a Supabase Bearer token. Returns the JWT payload."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")

    if not settings.SUPABASE_URL:
        raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured.")

    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unable to resolve signing key: {str(e)}")

    expected_issuer = f"{settings.SUPABASE_URL}/auth/v1"
    expected_audience = settings.SUPABASE_JWT_AUDIENCE
    verify_audience = bool(expected_audience)

    try:
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg] if alg else ["RS256"],
            issuer=expected_issuer,
            audience=expected_audience if verify_audience else None,
            options={"verify_aud": verify_audience},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid token audience")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    return decoded


def _resolve_role(email: Optional[str]) -> str:
    if not email:
        return "student"
    return "admin" if email.lower() in settings.ADMIN_EMAILS else "student"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Decode Bearer token, cache profile, return normalized user dict."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="User authentication required. Provide a valid Bearer token.",
        )

    payload = _decode_bearer(credentials.credentials)
    user_id = payload.get("sub") or payload.get("preferred_username")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # Keep the existing auth-provider cache populated so blog reads can decorate
    # responses with the author's display name.
    cache_user_profile_from_claims(user_id, payload)

    metadata = payload.get("user_metadata", {}) or {}
    email = payload.get("email")
    return {
        "user_id": user_id,
        "email": email,
        "first_name": metadata.get("first_name") or metadata.get("firstName") or "",
        "last_name": metadata.get("last_name") or metadata.get("lastName") or "",
        "role": _resolve_role(email),
        "raw": payload,
    }


async def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """Any authenticated user (student or admin)."""
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    """Backward-compatible shim — many existing handlers ask only for the user_id."""
    return user["user_id"]
