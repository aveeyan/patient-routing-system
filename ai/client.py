# ai/client.py

"""LLM Client for the system, based on Azure OpenAI API Services"""

# Standard Imports
from typing import Optional

# Third Party Imports
from loguru import logger
from openai import AsyncAzureOpenAI, OpenAIError

# Local Imports
from core.config import settings


## Module Level Singleton

_client: Optional[AsyncAzureOpenAI] = None

def _create_client() -> AsyncAzureOpenAI:
    """Create and configure the AsyncAzureOpenAI client.

    Uses settings from core.config (loaded from .env).
    Called once on first use, cached thereafter.
    """
    return AsyncAzureOpenAI(
        api_key=settings.azure_openai.api_key,
        api_version=settings.azure_openai.api_version,
        azure_endpoint=settings.azure_openai.endpoint,
        max_retries=3,
        timeout=settings.azure_openai.request_timeout,
    )


def get_client() -> AsyncAzureOpenAI:
    """Return the singleton Azure OpenAI client, creating it if necessary.

    Returns:
        AsyncAzureOpenAI: Configured async client instance.
    """
    global _client
    if _client is None:
        logger.info(
            "Initializing Azure OpenAI client",
            endpoint=settings.azure_openai.endpoint,
            deployment=settings.azure_openai.deployment_name,
            timeout=settings.azure_openai.request_timeout,
        )
        _client = _create_client()
    return _client


## Core Interaction

async def generate_response(
    system_prompt: str,
    user_message: str,
    *,
    max_tokens: int,
    temperature: Optional[float] = None,
) -> str:
    """
    Send a prompt to Azure OpenAI and return the response text.

    Args:
        system_prompt: The system prompt defining behavior and output format.
        user_message: The patient's input or context to process.
        max_tokens: Maximum tokens in the response (caller must specify).
        temperature: Override the default temperature. If None, uses config value.

    Returns:
        str: The LLM response content.

    Raises:
        RuntimeError: If the API call fails after retries.
    """
    client = get_client()
    temperature = temperature if temperature is not None else settings.azure_openai.temperature

    logger.debug(
        "Calling Azure OpenAI",
        deployment=settings.azure_openai.deployment_name,
        temperature=temperature,
        max_tokens=max_tokens,
        prompt_preview=system_prompt[:120],
    )

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content

        if content is None:
            logger.error("LLM returned empty response")
            raise RuntimeError("Azure OpenAI returned an empty response")

        logger.debug("LLM response received", length=len(content))
        return content

    except OpenAIError as e:
        logger.error("Azure OpenAI API error: {}", str(e))
        raise RuntimeError(f"Azure OpenAI call failed: {e}") from e
