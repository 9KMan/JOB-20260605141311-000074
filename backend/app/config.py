"""Application configuration from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "ATS Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ats_db"
    )
    DATABASE_ECHO: bool = Field(default=False)

    # JWT Authentication
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_EXTENSIONS: set[str] = Field(default={".pdf", ".docx", ".txt"})
    UPLOAD_DIR: str = Field(default="./uploads")

    # ATS Scoring
    ATS_ENGINE_MODULE: str = Field(default="backend.app.ats")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
