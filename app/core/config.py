from pydantic_settings import BaseSettings
from typing import List
import os

import json

def _default_cors_origins() -> List[str]:
    env_origins = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
    if env_origins:
        try:
            return json.loads(env_origins)
        except json.JSONDecodeError:
            return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "https://localhost:3000",
        "https://aistudentchapter.lk",
        "https://www.aistudentchapter.lk",
        "http://localhost",
        "https://chapters-frontend-three.vercel.app",
    ]

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVICE_STR: str = "/blogs"
    PROJECT_NAME: str = "Blog API"
    BACKEND_CORS_ORIGINS: List[str] = _default_cors_origins()
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./blog.db"  # Update this based on your database configuration
    
    # MongoDB settings
    BLOG_MONGODB_URL: str = "mongodb://localhost:27017"
    BLOG_MONGODB_DB_NAME: str = ""

    # Supabase auth settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_AUDIENCE: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    ALLOW_TRUSTED_X_USER_ID: bool = os.getenv("ALLOW_TRUSTED_X_USER_ID", "false").lower() == "true"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings() 