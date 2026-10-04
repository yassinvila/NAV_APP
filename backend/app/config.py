from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Navigation Backend"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    database_url: str = "sqlite:///./navigation.db"

    cors_allow_origins: str = "*"
    beta_access_pin: str = ""

    mapbox_access_token: str = ""
    mapbox_geocoding_url: str = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    mapbox_directions_url: str = "https://api.mapbox.com/directions/v5/mapbox/driving"

    model_name_or_path: str = ""
    model_input_prefix: str = ""
    hf_token: str = ""
    t5_nemo: str = ""
    t5_claude: str = ""
    hf_token_two: str = ""
    default_model_key: str = "T5_NEMO"

    default_route_profile: str = "driving"
    request_timeout_seconds: int = 15
    jwt_secret: str = "local-demo-jwt-secret-change-before-production"
    jwt_expiration_minutes: int = 1440
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
