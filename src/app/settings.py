from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    version: str = "0.0.1"

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

settings = Settings()