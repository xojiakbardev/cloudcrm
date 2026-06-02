"""Application configuration loaded from environment variables."""
import os
import socket
import uuid

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg2://crm:crm@db:5432/crm"

    # Security
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Instance identity (used to demonstrate load balancing / scaling)
    # Each running container gets a unique INSTANCE_ID so the dashboard can
    # show which backend instance served a given request.
    instance_id: str = os.getenv("INSTANCE_ID", socket.gethostname() or uuid.uuid4().hex[:8])
    instance_zone: str = os.getenv("INSTANCE_ZONE", "az-a")

    # CORS
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
