# core/config.py

"""Configurations for the overall system"""

# Standard Imports
from typing import Optional

# Third Party Imports
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local Imports


## Settings for Azure OpenAI
class AzureOpenAISettings(BaseSettings):
    """Settings for Azure OpenAI"""

    endpoint: str = Field(
        description="Azure OpenAI resource endpoint URL",
        examples=[
            "https://my-azure-openai-resource.openai.azure.com/"
        ]
    )

    api_key: str = Field(
        description="Azure OpenAI API key for authentication",
    )

    deployment_name: str = Field(
        description="Name of the Azure OpenAI deployment to use",
        default="gpt-4o"
    )

    api_version: str = Field(
        description="Azure OpenAI API version to use",
        default="2024-08-01-preview"
    )

    temperature: float = Field(
        description="Sampling temperature for response generation (0=deterministic, 2=creative)",
        default=0.1,
        ge=0.0,
        le=2.0
    )

    model_config = SettingsConfigDict(env_prefix="AZURE_OPENAI_")

## Settings for Azure Speech Services (optional)
class AzureSpeechSettings(BaseSettings):
    """Settings for Azure Speech Services"""

    key: Optional[str] = Field(
            default=None,
            description="Azure Speech service API key",
        )

    region: Optional[str] = Field(
            default=None,
            description="Azure Speech service region (e.g., eastus)",
        )

    model_config = SettingsConfigDict(env_prefix="AZURE_SPEECH_")

    @property
    def is_configured(self) -> bool:
        """Check if both key and region are provided"""
        return self.key is not None and self.region is not None


class Settings(BaseSettings):
    """Main settings for the patient routing system (loaded from env)"""

    # Azure services
    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    azure_speech: AzureSpeechSettings = Field(default_factory=AzureSpeechSettings)

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./triage.db",
        description="Database connection string",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Triage Pipeline
    confidence_threshold: int = Field(
        description="Minimum data points required for making a triage decision",
        default=3,
        ge=1,
        le=10
    )
    max_conversation_turns: int = Field(
        description="Maximum number of conversation turns to consider for triage",
        default=6,
        ge=2,
        le=20
    )

    # Model Configuration (.env settings)
    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
        )

## Singleton instance of settings
try:
    settings = Settings()
except ValidationError as e:
    print(
        "[FATAL] Failed to load configuration. Check the .env file.\n"
        f"Error:\n{e}"
    )
    raise SystemExit(1)
