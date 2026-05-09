# ai/client.py

"""LLM Client for the system, based on Azure OpenAI API Services"""

# Standard Imports
import asyncio
from typing import Optional

# Third Party Imports
from loguru import logger
from openai import AsyncOpenAI, OpenAIError

# Local Imports
from core.config import settings


## Custom Exceptions

class LLMError(RuntimeError):
    """Raised when the LLM client encounters an unrecoverable error."""


## Module Level Singleton

_client: Optional[AsyncOpenAI] = None
_client_lock = asyncio.Lock()


def _create_client() -> AsyncOpenAI:
    """Create and configure the AsyncOpenAI client."""
    return AsyncOpenAI(
        api_key=settings.azure_openai.api_key,
        base_url=f"{settings.azure_openai.endpoint}openai/v1/",
        max_retries=3,
        timeout=settings.azure_openai.request_timeout,
    )


async def get_client() -> AsyncOpenAI:
    """Return the singleton client, creating it if necessary."""
    global _client
    if _client is not None:
        return _client

    async with _client_lock:
        if _client is None:
            logger.info(
                "Initializing Azure OpenAI client",
                endpoint=settings.azure_openai.endpoint,
                deployment=settings.azure_openai.deployment_name,
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
    """Send a prompt to Azure OpenAI and return the response text."""
    client = await get_client()
    temp = temperature if temperature is not None else settings.azure_openai.temperature

    logger.debug(
        "Calling Azure OpenAI",
        deployment=settings.azure_openai.deployment_name,
        temperature=temp,
        max_tokens=max_tokens,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temp,
            max_tokens=max_tokens,
        )

        if not response.choices:
            logger.error("LLM returned no choices")
            raise LLMError("Azure OpenAI returned no choices (possible content filter)")

        content = response.choices[0].message.content

        if content is None:
            logger.error("LLM returned empty content")
            raise LLMError("Azure OpenAI returned an empty response")

        logger.debug("LLM response received", length=len(content))
        return content

    except LLMError:
        raise

    except OpenAIError as e:
        logger.error("Azure OpenAI API error", error=str(e))
        raise LLMError(f"Azure OpenAI call failed: {e}") from e
