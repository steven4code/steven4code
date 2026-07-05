"""Application configuration loaded from environment / .env file."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Provider
    use_mock_provider: bool = True

    # Google OAuth / Health API
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    oauth_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    oauth_token_url: str = "https://oauth2.googleapis.com/token"
    health_api_base: str = "https://health.googleapis.com/v4"
    health_scopes: str = (
        "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly "
        "https://www.googleapis.com/auth/googlehealth.sleep.readonly "
        "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"
    )

    # App
    database_url: str = "sqlite:///./data/health.db"
    frontend_origin: str = "http://localhost:5173"
    sync_lookback_days: int = 90

    @property
    def scopes_list(self) -> list[str]:
        return [s for s in self.health_scopes.split() if s]


settings = Settings()
