from typing import List, Dict
import time

from app.core.config import settings
from app.schemas.blog import AuthUserProfile

# Lightweight in-process profile cache populated from verified JWT claims.
_profile_cache: Dict[str, AuthUserProfile] = {}


def _build_username(user_id: str, claims: Dict | None = None) -> str:
    if claims:
        username = claims.get("preferred_username") or claims.get("email")
        if username:
            return username
    return f"user_{user_id[:8]}" if user_id else "anonymous"


def cache_user_profile_from_claims(user_id: str, claims: Dict) -> None:
    if not user_id:
        return

    metadata = claims.get("user_metadata", {}) if isinstance(claims.get("user_metadata"), dict) else {}
    app_metadata = claims.get("app_metadata", {}) if isinstance(claims.get("app_metadata"), dict) else {}
    
    user = AuthUserProfile(
        username=_build_username(user_id, claims),
        profilePicUrl=metadata.get("avatar_url") or metadata.get("picture") or claims.get("picture") or "",
        firstName=metadata.get("first_name") or claims.get("firstName") or "",
        lastName=metadata.get("last_name") or claims.get("lastName") or "",
        roles=app_metadata.get("roles", [])
    )
    _profile_cache[user_id] = user


def _fallback_user(user_id: str, default_username: str = "", default_profile_pic_url: str = "", default_first_name: str = "", default_last_name: str = "") -> AuthUserProfile:
    return AuthUserProfile(
        username=default_username or _build_username(user_id),
        profilePicUrl=default_profile_pic_url,
        firstName=default_first_name,
        lastName=default_last_name,
    )


async def get_all_users() -> List[AuthUserProfile]:
    return list(_profile_cache.values())


async def get_user_by_id(user_id: str) -> AuthUserProfile:
    if user_id in _profile_cache:
        return _profile_cache[user_id]
    return _fallback_user(user_id)


async def get_all_users_safely() -> List[AuthUserProfile]:
    return await get_all_users()


async def get_user_by_id_safely(user_id: str, *, default_username: str = "", default_profile_pic_url: str = "", default_first_name: str = "", default_last_name: str = "") -> AuthUserProfile:
    user = await get_user_by_id(user_id)
    if user:
        return user
    return _fallback_user(
        user_id,
        default_username=default_username,
        default_profile_pic_url=default_profile_pic_url,
        default_first_name=default_first_name,
        default_last_name=default_last_name,
    )


async def check_auth_provider_health() -> Dict:
    if not settings.SUPABASE_URL:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "authenticated": False,
            "service": "supabase-auth",
            "error": "SUPABASE_URL is not configured",
        }

    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    start_time = time.time()
    try:
        import urllib.request
        with urllib.request.urlopen(jwks_url, timeout=10) as response:
            status_code = response.getcode()
        response_time = round((time.time() - start_time) * 1000, 2)
        if status_code == 200:
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "authenticated": True,
                "service": "supabase-auth",
            }
        return {
            "status": "unhealthy",
            "response_time_ms": response_time,
            "authenticated": False,
            "service": "supabase-auth",
            "error": f"JWKS returned status {status_code}",
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "authenticated": False,
            "service": "supabase-auth",
            "error": str(exc),
        }
