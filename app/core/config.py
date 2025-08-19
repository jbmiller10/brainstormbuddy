from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRAINSTORMBUDDY_")

    data_dir: str = "projects"
    exports_dir: str = "exports"
    log_dir: str = "logs"
    enable_web_tools: bool = False


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
