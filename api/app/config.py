from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_API_KEY = "dev-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ribet:ribet@localhost:5432/ribet"
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "ribet-uploads"
    api_key: str = "dev-secret"
    admin_api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    storage_backend: str = "s3"
    max_upload_bytes: int = 50 * 1024 * 1024
    ribet_env: str = "local"
    ribet_app_url: str = "http://localhost:3000"
    resend_api_key: str = ""
    resend_from: str = "Ribet <reports@ribet.local>"
    default_brief_recipient: str = ""
    openai_api_key: str = ""
    ribet_narration: str = "off"
    ribet_narration_timeout_seconds: int = 90
    openai_model: str = "gpt-4o-mini"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ribet_env.strip().lower() == "production"


def validate_settings(cfg: Settings) -> None:
    """Fail fast when production is misconfigured."""
    if not cfg.is_production:
        return
    key = (cfg.api_key or "").strip()
    if not key or key == DEV_API_KEY:
        raise RuntimeError(
            "API_KEY must be set to a non-default secret when RIBET_ENV=production"
        )


settings = Settings()
validate_settings(settings)
