from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: str = "projects"
    exports_dir: str = "exports"
    log_dir: str = "logs"
    enable_web_tools: bool = False

    class Config:
        env_prefix = "BRAINSTORMBUDDY_"


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
