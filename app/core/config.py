from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRAINSTORMBUDDY_")

    data_dir: str = "projects"
    exports_dir: str = "exports"
    log_dir: str = "logs"
    enable_web_tools: bool = False

    # Onboarding validation constraints
    # Minimum project name length to ensure meaningful names
    min_project_name_length: int = 3
    # Maximum project name length to prevent overly long names
    max_project_name_length: int = 100
    # Maximum braindump length to prevent UI performance issues
    max_braindump_length: int = 10000
    # Minimum braindump length to ensure substantive content
    min_braindump_length: int = 10
    # Number of clarifying questions to generate during onboarding
    onboarding_questions_count: int = 5
    # Use fake LLM client for testing (until real client is implemented)
    use_fake_llm_client: bool = True


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
