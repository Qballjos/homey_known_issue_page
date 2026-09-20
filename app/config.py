import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Smart Home Known Issues"
    APP_URL: str = "http://localhost:8080"
    DATABASE_URL: str = "sqlite:///./data/known_issues.db"
    SECRET_KEY: str = "super-secret-known-issues-signing-key-change-in-production-12345"
    SESSION_COOKIE_NAME: str = "known_issues_session"
    COOKIE_SECURE: bool = False
    
    # SMTP Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@status.example.com"
    SMTP_TLS: bool = True
    
    # Initial Admin Provisioning
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123!"
    
    # Storage & directories
    DATA_DIR: str = "./data"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_SUBSCRIBE: str = "10/minute"
    
    # Seed data
    AUTO_SEED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
