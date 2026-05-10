# app/api/routes/speech.py

"""Speech transcription API route.

Exposes a single endpoint that accepts raw audio, delegates to
`ai.speech.transcribe_audio`, and returns the transcribed text.
The frontend places the text into the chat input box; the patient
confirms and sends it through the normal /triage/message flow.
"""

# Third Party Imports
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel

# Local Imports
from ai.client import LLMError
from ai.speech import MAX_AUDIO_BYTES, transcribe_audio

router = APIRouter()


## Response Schema

class TranscriptionResponse(BaseModel):
    text: str
    """Transcribed text ready to be placed in the chat input box."""


## Route Handler

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str | None = Form(
        default=None,
        description="Optional BCP-47 language tag, e.g. 'en-US'. Omit for auto-detect.",
    ),
):
    """Convert a speech recording to text.

    Accepts any audio format supported by Azure Speech Services
    (WAV, MP3, MP4, OGG, WebM, FLAC).  Returns the transcribed text
    so the frontend can populate the chat input box before the patient
    confirms and sends.

    **Size limit:** 25 MB.
    """
    audio_bytes = await audio.read()

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Maximum size is 25 MB.",
        )

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    content_type = audio.content_type or None

    logger.info(
        "Transcription request received",
        filename=audio.filename,
        size_bytes=len(audio_bytes),
        content_type=content_type,
        language=language or "auto",
    )

    try:
        text = await transcribe_audio(
            audio_bytes,
            content_type=content_type,
            language=language,
        )
        return TranscriptionResponse(text=text)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except LLMError as exc:
        logger.error("Transcription failed", error=str(exc))
        raise HTTPException(
            status_code=503,
            detail="Speech transcription service is temporarily unavailable. Please try again.",
        )
