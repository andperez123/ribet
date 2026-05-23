from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://ribet:ribet@localhost:5432/ribet"
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "ribet-uploads"
    api_key: str = "dev-secret"
    max_upload_bytes: int = 50 * 1024 * 1024


settings = Settings()
