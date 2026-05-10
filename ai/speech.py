# ai/speech.py

"""Speech-to-text transcription using faster-whisper (local, free, offline).

Receives raw audio bytes from the API layer, writes them to a temporary
file, runs faster-whisper inference, and returns the transcribed text.
No API keys or network calls are required.

Model is loaded once at process start and reused across requests
(see `_load_model`).  The default model size is controlled via
`settings.speech.whisper_model_size` (e.g. "base", "small", "medium").
"""

# Standard Imports
import asyncio
import tempfile
import os
from functools import lru_cache
from typing import Optional

# Third Party Imports
from faster_whisper import WhisperModel
from loguru import logger

# Local Imports
from ai.client import LLMError


## Supported MIME types → file extensions faster-whisper/ffmpeg can read
_AUDIO_EXTENSIONS: dict[str, str] = {
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "mp4",
    "audio/ogg": "ogg",
    "audio/webm": "webm",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
}

## Default MIME type assumed when the caller does not provide one.
_DEFAULT_CONTENT_TYPE = "audio/webm"


def _normalise_mime(content_type) -> str:
    """Strip codec parameters from a MIME type and return the bare type.

    Browsers often append codec info to the MIME type reported by
    MediaRecorder (e.g. "audio/webm;codecs=opus"). We only need the
    base type for extension lookup and validation.

    Examples:
        "audio/webm;codecs=opus"     -> "audio/webm"
        "audio/ogg; codecs=vorbis"   -> "audio/ogg"
        "audio/webm"                 -> "audio/webm"
        None                         -> "audio/webm"
    """
    if not content_type:
        return _DEFAULT_CONTENT_TYPE
    return content_type.split(";")[0].strip().lower()

## Maximum audio payload accepted (100 MB — local, so no hard API limit)
MAX_AUDIO_BYTES = 100 * 1024 * 1024


## Model Singleton


@lru_cache(maxsize=1)
def _load_model() -> WhisperModel:
    """Load and cache the WhisperModel.  Called once on first transcription.

    Model size is read from settings.speech.whisper_model_size.
    Recommended sizes:
      - "base"   — fastest, ~74 MB,  good for clear speech in quiet environments
      - "small"  — balanced, ~244 MB, recommended for production (default)
      - "medium" — higher accuracy, ~769 MB, slower on CPU

    Runs on CPU with int8 quantisation for broad compatibility.
    Switch to device="cuda", compute_type="float16" if a GPU is available.
    """
    try:
        from core.config import settings
        model_size: str = settings.whisper.model_size
    except (ImportError, AttributeError):
        model_size = "small"

    logger.info("Loading faster-whisper model", model_size=model_size)

    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",  # Quantised — good speed/accuracy trade-off on CPU
    )

    logger.info("faster-whisper model loaded", model_size=model_size)
    return model


## Public API


async def transcribe_audio(
    audio_bytes: bytes,
    *,
    content_type: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """Transcribe speech audio to text using faster-whisper (local Whisper).

    Writes audio to a temporary file (faster-whisper requires a real path,
    not a buffer), runs inference in a thread-pool executor so the asyncio
    event loop is not blocked, then returns the joined transcript.

    The result is intended to be placed directly into the chat input box
    on the frontend and passed to the triage pipeline as a normal patient
    message.

    Args:
        audio_bytes: Raw audio data.  Supported formats: WAV, MP3, MP4,
            OGG, WebM, FLAC.  Maximum size: 100 MB.
        content_type: MIME type of the audio (e.g. ``"audio/webm"``).
            Defaults to ``"audio/webm"`` when omitted.
        language: Whisper language code (e.g. ``"en"``, ``"ne"``).
            Note: Whisper uses short codes, not BCP-47 tags ("en" not "en-US").
            When omitted the model auto-detects the language.

    Returns:
        Transcribed text as a plain string.

    Raises:
        ValueError: Audio payload is empty, exceeds the size limit, or
            the supplied MIME type is not supported.
        LLMError: Transcription produced an empty result or raised an
            unexpected error during inference.
    """
    _validate_audio(audio_bytes, content_type)

    mime = _normalise_mime(content_type)
    extension = _AUDIO_EXTENSIONS[mime]

    logger.info(
        "Transcribing audio",
        size_bytes=len(audio_bytes),
        content_type=mime,
        language=language or "auto",
    )

    try:
        text = await asyncio.get_event_loop().run_in_executor(
            None,  # Use the default thread-pool executor
            _transcribe_sync,
            audio_bytes,
            extension,
            language,
        )
    except LLMError:
        raise
    except Exception as exc:
        logger.error("Unexpected transcription error", error=str(exc))
        raise LLMError(f"Transcription failed unexpectedly: {exc}") from exc

    if not text:
        logger.warning("faster-whisper returned an empty transcript")
        raise LLMError("Speech transcription returned an empty result")

    logger.info("Transcription complete", length=len(text))
    return text


## Private Helpers


def _transcribe_sync(
    audio_bytes: bytes,
    extension: str,
    language: Optional[str],
) -> str:
    """Run faster-whisper inference synchronously (called inside executor).

    Writes audio to a NamedTemporaryFile, runs the model, cleans up.

    Args:
        audio_bytes: Raw audio data.
        extension: File extension without a leading dot (e.g. ``"webm"``).
        language: Whisper language code, or None for auto-detect.

    Returns:
        Joined transcript string (may be empty if audio was silence).
    """
    model = _load_model()

    # faster-whisper requires a real file path — BytesIO is not accepted.
    with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        kwargs: dict = dict(
            beam_size=5,
            vad_filter=True,  # Skip silent segments — reduces hallucinations
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        if language:
            kwargs["language"] = language  # e.g. "en", "ne"

        segments, info = model.transcribe(tmp_path, **kwargs)

        logger.debug(
            "Whisper detection",
            detected_language=info.language,
            language_probability=round(info.language_probability, 3),
        )

        return " ".join(segment.text.strip() for segment in segments).strip()

    finally:
        os.unlink(tmp_path)  # Always clean up, even on error


def _validate_audio(audio_bytes: bytes, content_type: Optional[str]) -> None:
    """Raise ValueError for empty, oversized, or unsupported audio payloads."""
    if not audio_bytes:
        raise ValueError("Audio payload is empty")

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError(
            f"Audio payload is too large ({len(audio_bytes):,} bytes). "
            f"Maximum allowed size is {MAX_AUDIO_BYTES:,} bytes (100 MB)."
        )

    mime = _normalise_mime(content_type)
    if mime not in _AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(_AUDIO_EXTENSIONS))
        raise ValueError(
            f"Unsupported audio content type: {mime!r}. "
            f"Supported types: {supported}"
        )
