"""
Application settings.

Defaults declared inline are evaluated when the Settings *class body* runs,
which happens before pydantic-settings reads ``.env``. That timing meant a
plain ``os.getenv("ADMIN_EMAILS", "")`` would always return ``""`` locally,
silently dropping the admin allowlist. We now declare ADMIN_EMAILS /
BACKEND_CORS_ORIGINS as real pydantic fields so the env_file loader fills
them, and a single ``mode="before"`` validator handles both JSON arrays and
comma-separated forms.
"""
import json
import os
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


def _coerce_string_list(value: Union[str, list, None], *, lowercase: bool = False) -> List[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return [i.lower() for i in items] if lowercase else items

    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            items = [str(v).strip() for v in parsed if str(v).strip()]
            return [i.lower() for i in items] if lowercase else items
    except json.JSONDecodeError:
        pass

    items = [item.strip() for item in text.split(",") if item.strip()]
    return [i.lower() for i in items] if lowercase else items


_DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost",
    "https://aistudentchapter.lk",
    "https://www.aistudentchapter.lk",
    "https://chapters-frontend-three.vercel.app",
]


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVICE_STR: str = "/blogs"
    PROJECT_NAME: str = "Blog API"

    # CORS — read from env, fallback to defaults; localhost always preserved.
    BACKEND_CORS_ORIGINS: List[str] = list(_DEFAULT_CORS_ORIGINS)

    # Database settings
    DATABASE_URL: str = "sqlite:///./blog.db"

    # MongoDB settings
    BLOG_MONGODB_URL: str = "mongodb://localhost:27017"
    BLOG_MONGODB_DB_NAME: str = ""

    # Supabase auth settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_AUDIENCE: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")

    # Admin allowlist (case-insensitive emails)
    ADMIN_EMAILS: List[str] = []

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        parsed = _coerce_string_list(v)
        if not parsed:
            return list(_DEFAULT_CORS_ORIGINS)
        merged = parsed + [o for o in _DEFAULT_CORS_ORIGINS if o not in parsed and "localhost" in o]
        return merged

    @field_validator("ADMIN_EMAILS", mode="before")
    @classmethod
    def _parse_admin_emails(cls, v):
        return _coerce_string_list(v, lowercase=True)


settings = Settings()
