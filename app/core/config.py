from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, field_validator
from typing import List
from pathlib import Path

ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    API_V1_STR: str = "/api/v1"
    SERVICE_STR: str = "/blogs"
    PROJECT_NAME: str = "Blog API"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://localhost:3000",
            "http://localhost",
        ]
    )
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./blog.db"  # Update this based on your database configuration
    
    # MongoDB settings
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("BLOG_MONGODB_URL", "MONGODB_URL"),
    )
    MONGODB_DB_NAME: str = Field(
        default="blog_db",
        validation_alias=AliasChoices("BLOG_MONGODB_DB_NAME", "MONGODB_DB_NAME"),
    )

    # Supabase auth settings
    SUPABASE_URL: str = ""
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    ENVIRONMENT: str = "development"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DEBUG_ENDPOINTS_ENABLED: bool = False

    @field_validator("MONGODB_DB_NAME")
    @classmethod
    def validate_mongodb_db_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("BLOG_MONGODB_DB_NAME must be set and non-empty.")
        return cleaned

settings = Settings() 