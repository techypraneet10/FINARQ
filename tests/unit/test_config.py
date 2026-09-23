"""Unit tests for configuration loading and validation."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from financial_rag.common.types import Environment
from financial_rag.config.settings import (
    AppSettings,
    DatabaseSettings,
    LLMSettings,
    LoggingSettings,
    Settings,
)


@pytest.mark.unit
def test_default_settings_initialization() -> None:
    """Test default settings instantiate with expected default parameters."""
    settings = Settings()

    assert settings.app.name == "FINARQ"
    assert settings.app.version == "0.1.0"
    assert settings.app.environment == Environment.DEVELOPMENT
    assert settings.app.port == 8000
    assert settings.logging.level == "INFO"
    assert settings.logging.format == "text"
    assert settings.database.port == 5432
    assert settings.redis.port == 6379
    assert settings.qdrant.port == 6333
    assert settings.llm.provider == "mock"
    assert settings.embedding.dimension == 1536


@pytest.mark.unit
def test_environment_helper_properties() -> None:
    """Test helper properties correctly detect active environment."""
    dev_settings = Settings(app=AppSettings(environment=Environment.DEVELOPMENT))
    assert dev_settings.is_development is True
    assert dev_settings.is_production is False
    assert dev_settings.is_testing is False

    prod_settings = Settings(app=AppSettings(environment=Environment.PRODUCTION))
    assert prod_settings.is_development is False
    assert prod_settings.is_production is True
    assert prod_settings.is_testing is False

    test_settings = Settings(app=AppSettings(environment=Environment.TESTING))
    assert test_settings.is_development is False
    assert test_settings.is_production is False
    assert test_settings.is_testing is True


@pytest.mark.unit
def test_secret_string_masking() -> None:
    """Verify secrets are masked and do not reveal plaintext when stringified."""
    db_settings = DatabaseSettings(password="my_super_secret_password")  # type: ignore[arg-type]

    # str() or repr() should mask the value
    assert "my_super_secret_password" not in str(db_settings.password)
    assert "**********" in str(db_settings.password)
    # get_secret_value() exposes the underlying secret explicitly
    assert db_settings.password.get_secret_value() == "my_super_secret_password"


@pytest.mark.unit
def test_port_validation_bounds() -> None:
    """Verify port numbers outside valid TCP range raise validation errors."""
    with pytest.raises(ValidationError):
        AppSettings(port=70000)

    with pytest.raises(ValidationError):
        AppSettings(port=0)


@pytest.mark.unit
def test_temperature_validation_bounds() -> None:
    """Verify LLM temperature adheres to 0.0 - 2.0 bounds."""
    with pytest.raises(ValidationError):
        LLMSettings(temperature=3.5)

    with pytest.raises(ValidationError):
        LLMSettings(temperature=-0.5)


@pytest.mark.unit
def test_env_variable_override() -> None:
    """Test overriding configuration values via environment variables."""
    with patch.dict(
        os.environ,
        {
            "APP_NAME": "Custom SEC Analyzer",
            "APP_PORT": "9090",
            "LOG_LEVEL": "DEBUG",
            "LLM_PROVIDER": "openai",
        },
    ):
        settings = Settings(
            app=AppSettings(),
            logging=LoggingSettings(),
            llm=LLMSettings(),
        )
        assert settings.app.name == "Custom SEC Analyzer"
        assert settings.app.port == 9090
        assert settings.logging.level == "DEBUG"
        assert settings.llm.provider == "openai"
