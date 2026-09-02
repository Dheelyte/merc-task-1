from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOTES_")

    database_url: str = f"sqlite:///{BASE_DIR / 'notes.db'}"
    jwt_secret: str = "change-me-in-prod-use-a-long-random-string"
    jwt_ttl_minutes: int = 60
    config_path: Path = BASE_DIR / "config.yaml"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def load_file_config() -> dict:
    with open(get_settings().config_path) as fh:
        return yaml.safe_load(fh) or {}
