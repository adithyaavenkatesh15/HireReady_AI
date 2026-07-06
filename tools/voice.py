"""
tools/voice.py

Voice tool (not an agent) providing speech-to-text and text-to-speech
capability via ElevenLabs.

Workflow:
    User speaks -> speech_to_text() -> main.py -> LangGraph -> Response
    -> text_to_speech() -> save_audio() -> Play Audio
"""

import os
import time
import requests

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    ELEVENLABS_STT_URL,
    ELEVENLABS_TTS_URL,
    AUDIO_DIR,
)


class VoiceError(Exception):
    """Raised when a voice operation (STT or TTS) fails."""


def _require_api_key() -> None:
    if not ELEVENLABS_API_KEY:
        raise VoiceError(
            "ELEVENLABS_API_KEY is not set. Please configure it in .env."
        )


def speech_to_text(audio_file_path: str) -> str:
    """
    Convert a recorded audio file into text using ElevenLabs Speech-to-Text.

    Args:
        audio_file_path: Path to a local audio file (wav/mp3).

    Returns:
        str: The transcribed text.

    Raises:
        VoiceError: If the API key is missing or the request fails.
    """
    _require_api_key()

    if not os.path.exists(audio_file_path):
        raise VoiceError(f"Audio file not found: {audio_file_path}")

    headers = {"xi-api-key": ELEVENLABS_API_KEY}

    try:
        with open(audio_file_path, "rb") as audio_file:
            files = {"file": audio_file}
            data = {"model_id": "scribe_v1"}

            response = requests.post(
                ELEVENLABS_STT_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=60,
            )
            response.raise_for_status()

        result = response.json()
        return result.get("text", "").strip()

    except requests.exceptions.RequestException as exc:
        raise VoiceError(f"Speech-to-text request failed: {exc}") from exc


def text_to_speech(text: str, output_filename: str = None) -> str:
    """
    Convert text into speech audio using ElevenLabs Text-to-Speech and
    save the result to the audio directory.

    Args:
        text: Text to synthesize into speech.
        output_filename: Optional filename for the saved audio file.

    Returns:
        str: Full path to the saved audio file.

    Raises:
        VoiceError: If the API key is missing, text is empty, or the
        request fails.
    """
    _require_api_key()

    if not text or not text.strip():
        raise VoiceError("Cannot synthesize speech from empty text.")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    url = f"{ELEVENLABS_TTS_URL}/{ELEVENLABS_VOICE_ID}"

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        return save_audio(response.content, output_filename)

    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == 402:
            raise VoiceError(
                "Text-to-speech failed because ElevenLabs requires billing/credits for this account."
            ) from exc
        raise VoiceError(f"Text-to-speech request failed: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise VoiceError(f"Text-to-speech request failed: {exc}") from exc


def save_audio(audio_bytes: bytes, output_filename: str = None) -> str:
    """
    Save raw audio bytes to the audio directory.

    Args:
        audio_bytes: Raw MP3 audio content.
        output_filename: Optional filename. Auto-generated if omitted.

    Returns:
        str: Full path to the saved audio file.
    """
    if not output_filename:
        output_filename = f"speech_{int(time.time())}.mp3"

    output_path = os.path.join(AUDIO_DIR, output_filename)

    with open(output_path, "wb") as audio_file:
        audio_file.write(audio_bytes)

    return output_path


def load_audio_bytes(audio_path: str) -> bytes:
    """
    Load a saved audio file back into memory (used for Streamlit's
    audio player and download button).
    """
    if not os.path.exists(audio_path):
        raise VoiceError(f"Audio file not found: {audio_path}")

    with open(audio_path, "rb") as audio_file:
        return audio_file.read()
