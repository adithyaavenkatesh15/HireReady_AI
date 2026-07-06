"""
tools/translator.py

Translation tool (not an agent) that converts the final analysis report
into the user's selected language using OpenRouter.

Supports: English, Tamil, Hindi, Telugu, Kannada, Malayalam.
"""

from config import OPENROUTER_API_KEY, SUPPORTED_LANGUAGES
from tools.utils import LLMError, call_llm


class TranslationError(Exception):
    """Raised when the translation request fails."""


def get_language_code(language_name: str) -> str:
    """
    Convert a human-readable language name (e.g. "Tamil") into the
    target language label expected by the translation prompt.
    """
    return SUPPORTED_LANGUAGES.get(language_name, "English")


def translate_text(text: str, target_language: str) -> str:
    """
    Translate a single block of text into the target language.

    Args:
        text: Source text (assumed to be in English).
        target_language: Human-readable target language name, e.g. "Tamil".

    Returns:
        str: Translated text. Falls back to the original text if
        translation fails or the target language is English.
    """
    if not text:
        return text

    if target_language == "English":
        return text

    target_label = get_language_code(target_language)

    if not OPENROUTER_API_KEY:
        raise TranslationError(
            "OPENROUTER_API_KEY is not set. Please configure it in .env."
        )

    system_prompt = (
        "You are a professional translator. Translate the provided text into "
        f"{target_label}. Preserve the original meaning, tone, and structure. "
        "Return only the translated text with no extra commentary."
    )

    try:
        translated_text = call_llm(system_prompt, text, temperature=0.2)
    except LLMError as exc:
        raise TranslationError(str(exc)) from exc

    if not translated_text:
        raise TranslationError("OpenRouter returned an empty translation.")

    return translated_text.strip()


def translate_report_sections(report: dict, target_language: str) -> dict:
    """
    Translate the human-readable text fields of a final report dictionary
    while leaving numeric scores and structural keys untouched.

    Args:
        report: The combined final report dictionary.
        target_language: Human-readable target language name.

    Returns:
        dict: A new dictionary with translatable string fields translated.
    """
    if target_language == "English":
        return report

    translated_report = dict(report)

    translatable_keys = [
        "executive_summary",
        "formatting_feedback",
        "readability_feedback",
        "section_order_feedback",
        "keyword_density_feedback",
    ]

    for key in translatable_keys:
        if key in translated_report and isinstance(translated_report[key], str):
            try:
                translated_report[key] = translate_text(translated_report[key], target_language)
            except TranslationError:
                # Fall back gracefully: keep original text if translation fails
                continue

    translatable_list_keys = ["suggestions", "strengths", "weaknesses"]
    for key in translatable_list_keys:
        if key in translated_report and isinstance(translated_report[key], list):
            translated_items = []
            for item in translated_report[key]:
                if isinstance(item, str):
                    try:
                        translated_items.append(translate_text(item, target_language))
                    except TranslationError:
                        translated_items.append(item)
                else:
                    translated_items.append(item)
            translated_report[key] = translated_items

    return translated_report
