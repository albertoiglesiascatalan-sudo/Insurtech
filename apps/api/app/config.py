from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://insurtech:insurtech@localhost:5432/insurtech"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis
    redis_url: str = "redis://localhost:6379"

    # OpenAI
    openai_api_key: str = ""
    openai_model_summarize: str = "gpt-4o-mini"
    openai_model_categorize: str = "gpt-4o-mini"
    openai_model_newsletter: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Resend
    resend_api_key: str = ""
    resend_from_email: str = "newsletter@insurtech.news"
    resend_from_name: str = "InsurTech Intelligence"

    # Auth
    secret_key: str = "changeme-in-production-use-32-chars-minimum"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # App
    admin_email: str = "admin@insurtech.news"
    environment: str = "development"
    app_url: str = "http://localhost:3000"

    # Ingestion
    ingestion_interval_minutes: int = 30
    deduplication_threshold: float = 0.92


@lru_cache
def get_settings() -> Settings:
    return Settings()
