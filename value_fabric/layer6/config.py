"""Configuration for Layer 6 Benchmark Service."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from value_fabric.shared.security.neo4j import validate_neo4j_aura_config


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8006, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(..., alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    neo4j_max_pool_size: int = Field(default=50, alias="NEO4J_MAX_POOL_SIZE")

    @field_validator("neo4j_password")
    @classmethod
    def validate_neo4j_password(cls, v: str | None) -> str:
        """Validate that Neo4j password is configured."""
        if v is None or v.strip() == "":
            raise ValueError(
                "NEO4J_PASSWORD environment variable must be set. "
                "Cannot use empty or None password for security reasons."
            )
        if v == "password":
            raise ValueError(
                "NEO4J_PASSWORD cannot be 'password'. "
                "Please set a secure password via NEO4J_PASSWORD environment variable."
            )
        return v

    @model_validator(mode="after")
    def validate_prod_neo4j_aura(self) -> "Settings":
        """Production/staging must use managed Aura, not in-cluster Neo4j."""
        validate_neo4j_aura_config(
            uri=self.neo4j_uri,
            password=self.neo4j_password,
            environment=os.getenv("ENVIRONMENT") or os.getenv("ENV"),
        )
        return self

    @property
    def neo4j_auth(self) -> tuple[str, str]:
        """Return Neo4j authentication tuple."""
        return (self.neo4j_user, self.neo4j_password)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
