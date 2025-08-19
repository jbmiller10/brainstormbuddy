from typing import Any

from app.core.config import Settings, load_settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.data_dir == "projects"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False


def test_env_override(monkeypatch: Any) -> None:
    monkeypatch.setenv("BRAINSTORMBUDDY_DATA_DIR", "custom_projects")
    monkeypatch.setenv("BRAINSTORMBUDDY_EXPORTS_DIR", "custom_exports")
    monkeypatch.setenv("BRAINSTORMBUDDY_LOG_DIR", "custom_logs")
    monkeypatch.setenv("BRAINSTORMBUDDY_ENABLE_WEB_TOOLS", "true")

    settings = Settings()
    assert settings.data_dir == "custom_projects"
    assert settings.exports_dir == "custom_exports"
    assert settings.log_dir == "custom_logs"
    assert settings.enable_web_tools is True


def test_partial_env_override(monkeypatch: Any) -> None:
    monkeypatch.setenv("BRAINSTORMBUDDY_DATA_DIR", "override_data")

    settings = Settings()
    assert settings.data_dir == "override_data"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False


def test_load_settings_singleton() -> None:
    settings1 = load_settings()
    settings2 = load_settings()
    assert settings1 is settings2


def test_load_settings_returns_settings_instance() -> None:
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.data_dir == "projects"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False
