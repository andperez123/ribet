from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
