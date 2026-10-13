from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pathlib import Path


BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str
    gemini_api_keys: Optional[str] = None
    gemini_api_key_2: Optional[str] = None
    gemini_api_key_3: Optional[str] = None
    gemini_api_key_4: Optional[str] = None
    gemini_api_key_5: Optional[str] = None
    gemini_api_key_6: Optional[str] = None
    gemini_api_key_7: Optional[str] = None
    gemini_api_key_8: Optional[str] = None
    gemini_api_key_9: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"

    # MongoDB
    mongodb_uri: str
    mongodb_database: str = "contentflow_ai"

    # JWT
    jwt_secret: str
    access_token_expire_minutes: int = 1440

    # URLs
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    model_config = {
        "env_file": BACKEND_ENV_FILE,
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
