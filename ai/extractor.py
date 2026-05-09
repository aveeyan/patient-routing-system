# ai/extractor.py

"""Symptom extraction and follow-up generation using Azure OpenAI.

Handles the AI layer: calling the LLM for structured symptom extraction
and dynamic follow-up question generation. All LLM interaction flows
through ai/client.py; this module manages prompts, parsing, and validation.
"""

# Standard Imports
import json
import re
from typing import Optional

# Third Party Imports
from loguru import logger

# Local Imports
from ai.client import generate_response
from ai.prompts import FOLLOW_UP_PROMPT, SYMPTOM_EXTRACTION_PROMPT
from schemas.triage import ExtractedSymptoms, Symptom


## Token Budgets
# Extraction produces a small JSON object; 384 tokens is generous.
_EXTRACTION_MAX_TOKENS = 384
# Follow-up produces a single question; 128 tokens is more than enough.
_FOLLOW_UP_MAX_TOKENS = 128

## Confidence Constants
# Returned when extraction fails entirely (parse error, API error).
_FAILED_CONFIDENCE = 0.0
# Threshold below which low_confidence_reason must be populated.
# Must match the threshold documented in ExtractedSymptoms.low_confidence_reason.
_LOW_CONFIDENCE_THRESHOLD = 0.7

## Maximum conversation history turns to include as context.
_MAX_HISTORY_TURNS = 6


## Public API


async def extract_symptoms(
    user_message: str,
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> ExtractedSymptoms:
    """Extract structured symptoms from a patient's message using the LLM.

    Builds the extraction prompt, calls Azure OpenAI, parses the JSON
    response, and validates it into an ExtractedSymptoms object.

    Args:
        user_message: The latest raw text from the patient.
        conversation_history: Previous turns in the conversation, if any.
            Each dict has "role" ("user" or "bot") and "content" keys.

    Returns:
        ExtractedSymptoms with canonical symptom names, severity, duration,
        body site, negated symptoms, and confidence. Returns an empty
        structure with confidence=0.0 if extraction fails.
    """
    prompt_text = _build_extraction_input(user_message, conversation_history)

    logger.info(
        "Extracting symptoms",
        message_length=len(user_message),
        has_history=conversation_history is not None,
    )

    try:
        raw_response = await generate_response(
            system_prompt=SYMPTOM_EXTRACTION_PROMPT,
            user_message=prompt_text,
            max_tokens=_EXTRACTION_MAX_TOKENS,
        )

        parsed = _parse_json_response(raw_response)
        extracted = _validate_and_build(parsed, user_message)

        logger.info(
            "Extraction complete",
            primary_count=len(extracted.primary_symptoms),
            associated_count=len(extracted.associated_symptoms),
            negated_count=len(extracted.negated_symptoms),
            confidence=extracted.confidence,
        )

        return extracted

    except Exception as exc:
        logger.error(
            "Extraction failed, returning empty result",
            error=str(exc),
            message_length=len(user_message),
        )
        return ExtractedSymptoms(
            raw_text=user_message,
            confidence=_FAILED_CONFIDENCE,
            low_confidence_reason=f"Extraction error: {exc}",
        )


async def generate_follow_up(
    symptoms_summary: str,
    missing_info: str,
    negated_symptoms: list[str],
) -> str:
    """Generate ONE dynamic follow-up question to gather missing triage information.

    Formats the follow-up prompt with what we know, what we need, and what
    the patient has already denied, then calls the LLM to produce a single
    natural-language question.

    Args:
        symptoms_summary: Human-readable summary of what we have extracted.
        missing_info: Description of what information is still needed.
        negated_symptoms: Canonical names of symptoms already denied.

    Returns:
        A single follow-up question as a plain string.
    """
    negated_str = ", ".join(negated_symptoms) if negated_symptoms else "(none)"

    try:
        prompt = FOLLOW_UP_PROMPT.format(
            symptoms_summary=symptoms_summary,
            missing_info=missing_info,
            negated_symptoms=negated_str,
        )
    except KeyError as exc:
        logger.error("FOLLOW_UP_PROMPT format key missing", key=str(exc))
        return "Could you tell me more about what you are experiencing?"

    logger.info("Generating follow-up question")

    try:
        question = await generate_response(
            system_prompt=prompt,
            user_message=f"Patient symptoms: {symptoms_summary}\nMissing information: {missing_info}",
            max_tokens=_FOLLOW_UP_MAX_TOKENS,
        )

        question = question.strip().strip('"').strip("'")

        logger.info("Follow-up generated", question_length=len(question))
        return question

    except Exception as exc:
        logger.error("Follow-up generation failed, using fallback", error=str(exc))
        return "Could you tell me more about what you are experiencing?"


## Private Helpers — Input Construction


def _build_extraction_input(
    user_message: str,
    conversation_history: Optional[list[dict[str, str]]],
) -> str:
    """Build the full input string for the extraction prompt.

    Prepends recent conversation history so the LLM has context about
    what was already discussed. Truncates to _MAX_HISTORY_TURNS and logs
    when truncation occurs.

    Args:
        user_message: The latest patient message.
        conversation_history: Previous turns in the conversation.

    Returns:
        Formatted string ready for the LLM.
    """
    if not conversation_history:
        return f"User Message: {user_message}"

    total_turns = len(conversation_history)
    if total_turns > _MAX_HISTORY_TURNS:
        logger.debug(
            "Conversation history truncated for extraction context",
            total_turns=total_turns,
            included_turns=_MAX_HISTORY_TURNS,
        )

    history_lines: list[str] = []
    for turn in conversation_history[-_MAX_HISTORY_TURNS:]:
        role = "Patient" if turn["role"] == "user" else "Bot"
        history_lines.append(f"{role}: {turn['content']}")

    history_text = "\n".join(history_lines)
    return (
        f"Conversation so far:\n{history_text}\n\n"
        f"Latest User Message: {user_message}"
    )


## Private Helpers — JSON Parsing


def _parse_json_response(raw: str) -> dict:
    """Parse a JSON response from the LLM, handling common formatting issues.

    LLMs frequently wrap JSON in markdown code blocks or include trailing
    commas. This function applies progressively more aggressive recovery
    strategies before giving up.

    Args:
        raw: Raw string response from the LLM.

    Returns:
        Parsed dictionary, or an empty dict if parsing fails.
    """
    cleaned = raw.strip()

    # Strategy 1: Extract from markdown code blocks
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    # Strategy 2: Remove trailing commas before closing brackets/braces
    cleaned = re.sub(r",\s*(\]|\})", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed, attempting recovery", error=str(exc))

    # Strategy 3: Find anything that looks like a JSON object
    brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.error("Could not parse LLM response as JSON", raw_length=len(raw))
    return {}


## Private Helpers — Validation


def _validate_and_build(parsed: dict, raw_text: str) -> ExtractedSymptoms:
    """Build an ExtractedSymptoms from parsed JSON, validating along the way.

    Drops unknown fields. Fills defaults for missing fields. Normalizes
    symptom names to lowercase with underscores. Never raises — always
    returns a valid ExtractedSymptoms, even if empty.

    Args:
        parsed: Parsed JSON dictionary from the LLM response.
        raw_text: Original user message for context.

    Returns:
        Validated ExtractedSymptoms object.
    """
    try:
        primary = _build_symptom_list(parsed.get("primary_symptoms", []))
        associated = _build_symptom_list(parsed.get("associated_symptoms", []))
        negated = _build_negated_list(parsed.get("negated_symptoms", []))

        confidence = _clamp_confidence(parsed.get("confidence", 1.0))

        low_confidence_reason: Optional[str] = None

        if confidence < _LOW_CONFIDENCE_THRESHOLD:
            low_confidence_reason = (
                f"LLM reported low confidence ({confidence:.2f}). "
                "Symptoms may be vague, ambiguous, or unclear."
            )

        if not primary and not associated:
            low_confidence_reason = (
                low_confidence_reason
                or "No symptoms could be extracted from the message."
            )

        return ExtractedSymptoms(
            primary_symptoms=primary,
            associated_symptoms=associated,
            negated_symptoms=negated,
            raw_text=raw_text,
            confidence=confidence,
            low_confidence_reason=low_confidence_reason,
        )

    except Exception as exc:
        logger.error("Validation failed during extraction build", error=str(exc))
        return ExtractedSymptoms(
            raw_text=raw_text,
            confidence=_FAILED_CONFIDENCE,
            low_confidence_reason=f"Validation error: {exc}",
        )


def _build_symptom_list(raw_symptoms: list) -> list[Symptom]:
    """Convert a list of raw symptom dicts into validated Symptom objects.

    Logs a warning when severity is missing and uses "moderate" as a
    conservative fallback, since missing severity is a data quality signal.

    Args:
        raw_symptoms: List of dicts from the LLM JSON.

    Returns:
        List of Symptom objects (invalid entries are skipped with a debug log).
    """
    symptoms: list[Symptom] = []

    for item in raw_symptoms:
        if not isinstance(item, dict):
            continue
        if not item.get("name"):
            continue

        if "severity" not in item:
            logger.warning(
                "Symptom missing severity field, defaulting to moderate",
                name=item.get("name"),
            )

        try:
            symptoms.append(
                Symptom(
                    name=str(item["name"]).strip().lower().replace(" ", "_"),
                    severity=item.get("severity", "moderate"),
                    duration=item.get("duration"),
                    body_site=item.get("body_site"),
                )
            )
        except Exception as exc:
            logger.debug("Skipping invalid symptom entry", entry=item, error=str(exc))

    return symptoms


def _build_negated_list(raw_negated: list) -> list[str]:
    """Convert a list of raw negated symptom entries into canonical strings.

    Args:
        raw_negated: List of strings from the LLM JSON.

    Returns:
        List of normalized symptom name strings.
    """
    negated: list[str] = []

    for item in raw_negated:
        if isinstance(item, str) and item.strip():
            negated.append(item.strip().lower().replace(" ", "_"))

    return negated


def _clamp_confidence(value: object) -> float:
    """Safely convert and clamp a confidence value to [0.0, 1.0].

    Args:
        value: Raw confidence value from the LLM (may be int, float, str, or None).

    Returns:
        Float in range [0.0, 1.0].
    """
    try:
        confidence = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _FAILED_CONFIDENCE

    return max(0.0, min(1.0, confidence))
