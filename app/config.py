from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_dir: Path = Path("logs")

    model_config = SettingsConfigDict(
        env_prefix="CALL_TRACE_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()