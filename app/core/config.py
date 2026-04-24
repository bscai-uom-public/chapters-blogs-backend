from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVICE_STR: str = "/blogs"
    PROJECT_NAME: str = "Blog API"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://localhost:3000",
        "https://aistudentchapter.lk",
        "https://www.aistudentchapter.lk",
        "http://localhost",
    ]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./blog.db"  # Update this based on your database configuration
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("BLOG_MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("BLOG_MONGODB_DB_NAME", "")

    # Supabase auth settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_AUDIENCE: str = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    ALLOW_TRUSTED_X_USER_ID: bool = os.getenv("ALLOW_TRUSTED_X_USER_ID", "false").lower() == "true"

    class Config:
        case_sensitive = True

settings = Settings() 