"""
Core configuration module for The Good Shepherd backend.
Loads settings from environment variables.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(default="postgresql://goodshepherd:goodshepherd@localhost:5432/goodshepherd")
    database_echo: bool = Field(default=False)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # JWT Authentication
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=1440)  # 24 hours

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # LLM Configuration
    openai_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4-turbo-preview")
    llm_max_tokens: int = Field(default=2000)
    llm_temperature: float = Field(default=0.3)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Worker Configuration
    rss_worker_interval_minutes: int = Field(default=30)
    news_worker_interval_minutes: int = Field(default=60)
    gov_worker_interval_minutes: int = Field(default=120)
    social_worker_interval_minutes: int = Field(default=15)

    # Security
    allowed_hosts: str = Field(default="localhost,127.0.0.1")
    rate_limit_per_minute: int = Field(default=60)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_allowed_hosts(self) -> List[str]:
        """Parse allowed hosts from comma-separated string."""
        return [host.strip() for host in self.allowed_hosts.split(",")]


# Global settings instance
settings = Settings()
