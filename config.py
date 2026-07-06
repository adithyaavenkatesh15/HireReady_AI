"""
config.py

Centralized configuration loader for HireReady AI.

Loads all required environment variables from a local .env file and
exposes them as module-level constants so the rest of the app never
has to touch os.getenv() directly.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv()

# ---------------------------------------------------------------------
# LLM Configuration (OpenRouter)
# ---------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b")

# ---------------------------------------------------------------------
# Voice Configuration (ElevenLabs)
# ---------------------------------------------------------------------
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# ---------------------------------------------------------------------
# Translation Configuration (OpenRouter)
# ---------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "English": "English",
    "Tamil": "Tamil",
    "Hindi": "Hindi",
    "Telugu": "Telugu",
    "Kannada": "Kannada",
    "Malayalam": "Malayalam",
}

# ---------------------------------------------------------------------
# File System Paths
# ---------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

for _directory in (UPLOADS_DIR, REPORTS_DIR, AUDIO_DIR, ASSETS_DIR):
    os.makedirs(_directory, exist_ok=True)


def validate_config() -> list:
    """
    Check which required API keys are missing.

    Returns:
        list[str]: Names of missing environment variables. Empty list
        means all required keys are present.
    """
    missing = []

    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not ELEVENLABS_API_KEY:
        missing.append("ELEVENLABS_API_KEY")

    return missing
