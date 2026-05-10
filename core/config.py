# core/config.py

"""Configurations for the overall system"""

# Standard Imports
import sys
from pathlib import Path
from typing import Literal, Optional

# Third Party Imports
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = str(Path(__file__).resolve().parent.parent / ".env")

## Settings for Azure OpenAI
class AzureOpenAISettings(BaseSettings):
    """Settings for Azure OpenAI"""

    endpoint: str = Field(
        description="Azure OpenAI resource endpoint URL",
        examples=["https://my-azure-openai-resource.openai.azure.com/"],
    )
    api_key: str = Field(
        description="Azure OpenAI API key for authentication",
    )
    deployment_name: str = Field(
        default="gpt-4.1-mini",
        description="Name of the Azure OpenAI deployment to use",
    )
    api_version: str = Field(
        default="2024-08-01-preview",
        description="Azure OpenAI API version to use",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for response generation (0=deterministic, 2=creative)",
    )
    request_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="Timeout in seconds for each Azure OpenAI API call",
    )

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        extra="ignore",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8"
    )


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

    model_config = SettingsConfigDict(
        env_prefix="AZURE_SPEECH_",
        extra="ignore",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8"
    )

    @property
    def is_configured(self) -> bool:
        """Return True if both key and region are provided."""
        return self.key is not None and self.region is not None


## Settings for Whisper Speech-to-Text
class WhisperSpeechSettings(BaseSettings):
    """Settings for local faster-whisper transcription."""

    model_size: str = Field(
        default="small",
        description="Whisper model size: base (~74 MB), small (~244 MB), medium (~769 MB)",
    )

    model_config = SettingsConfigDict(
        env_prefix="WHISPER_SPEECH_",
        extra="ignore",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
    )


## Main Settings
class Settings(BaseSettings):
    """Main settings for the patient routing system (loaded from env)"""

    azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
    azure_speech: AzureSpeechSettings = Field(default_factory=AzureSpeechSettings)
    whisper: WhisperSpeechSettings = Field(default_factory=WhisperSpeechSettings)

    database_url: str = Field(
        default="sqlite+aiosqlite:///./triage.db",
        description="Database connection string",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    log_file: Optional[str] = Field(
        default=None,
        description=(
            "Optional path for a persistent log file. "
            "If set, all log output is also written here. "
            "Example: logs/triage.log"
        ),
    )

    min_data_points: int = Field(
        default=3,
        ge=1,
        le=10,
        description=(
            "Minimum number of symptom data points required before the pipeline "
            "attempts a triage decision. Not related to LLM confidence scores."
        ),
    )
    max_conversation_turns: int = Field(
        default=6,
        ge=2,
        le=20,
        description="Maximum number of conversation turns before forcing a triage decision",
    )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


## Singleton
try:
    settings = Settings()
except ValidationError as e:
    sys.stderr.write(
        "[FATAL] Failed to load configuration. Check the .env file.\n"
        f"Error:\n{e}\n"
    )
    raise SystemExit(1)
