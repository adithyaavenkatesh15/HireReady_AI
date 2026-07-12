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


def translate_batch(texts: list, target_language: str) -> list:
    """
    Translate a list of texts into the target language in a single LLM call.
    """
    if not texts:
        return []

    if target_language == "English":
        return texts

    target_label = get_language_code(target_language)

    if not OPENROUTER_API_KEY:
        raise TranslationError(
            "OPENROUTER_API_KEY is not set. Please configure it in .env."
        )

    import json
    input_json = json.dumps({"texts": texts}, indent=2)

    system_prompt = (
        "You are a professional translator. Translate the array of texts provided in the JSON "
        f"into {target_label}. Preserve the original meaning, tone, formatting, and structure. "
        "Keep technical terms (like programming languages, frameworks, tools) in English where appropriate for professional resumes. "
        "Return the output as a valid JSON object matching the input structure: "
        '{"translations": ["translated_text_1", "translated_text_2", ...]} '
        "Do not include any markdown formatting, backticks, or extra conversational text."
    )

    try:
        response = call_llm(system_prompt, input_json, temperature=0.2)
        # Parse the JSON response
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        parsed = json.loads(clean_response)
        translations = parsed.get("translations", [])
        if len(translations) == len(texts):
            return translations
        else:
            raise TranslationError(
                f"Translation count mismatch: expected {len(texts)}, got {len(translations)}"
            )
    except Exception as exc:
        raise TranslationError(str(exc)) from exc


def translate_report_sections(report: dict, target_language: str) -> dict:
    """
    Translate the human-readable text fields of a final report dictionary
    while leaving numeric scores and structural keys untouched.
    Uses batch translation for performance and fallback.
    """
    if target_language == "English":
        return report

    # Define all translatable keys
    translatable_keys = [
        "executive_summary",
        "formatting_feedback",
        "readability_feedback",
        "section_order_feedback",
        "keyword_density_feedback",
        "improved_summary",
        "difficulty_level",
    ]
    
    translatable_list_keys = [
        "suggestions",
        "strengths",
        "weaknesses",
        "missing_sections",
        "missing_keywords",
        "missing_technologies",
        "missing_technical_skills",
        "missing_soft_skills",
        "recommended_certifications",
        "learning_resources",
        "career_roadmap",
        "bullet_point_rewrites",
        "grammar_fixes",
        "action_verb_suggestions",
        "hr_questions",
        "technical_questions",
        "project_questions",
        "behavioral_questions",
        "expected_answers",
    ]

    # Collect texts to translate with a mapping to stitch them back
    texts_to_translate = []
    mapping = []  # List of tuples: (type_str, key, index)

    for key in translatable_keys:
        if key in report and isinstance(report[key], str) and report[key].strip():
            texts_to_translate.append(report[key])
            mapping.append(('string', key, None))

    for key in translatable_list_keys:
        if key in report and isinstance(report[key], list):
            for i, item in enumerate(report[key]):
                if isinstance(item, str) and item.strip():
                    texts_to_translate.append(item)
                    mapping.append(('list', key, i))
                elif isinstance(item, dict):
                    # Handle dictionary items (like bullet rewrites)
                    for dict_key in ["original", "improved"]:
                        if dict_key in item:
                            val = item[dict_key]
                            if isinstance(val, str) and val.strip():
                                texts_to_translate.append(val)
                                mapping.append(('dict_string', (key, i, dict_key), None))
                            elif isinstance(val, list):
                                for j, sub_item in enumerate(val):
                                    if isinstance(sub_item, str) and sub_item.strip():
                                        texts_to_translate.append(sub_item)
                                        mapping.append(('dict_list', (key, i, dict_key, j), None))

    if not texts_to_translate:
        return report

    # Perform batch translation
    translated_texts = []
    try:
        translated_texts = translate_batch(texts_to_translate, target_language)
    except Exception as exc:
        # Fall back to element-by-element translation if batch translation fails
        # to ensure resilience.
        translated_texts = []
        for text in texts_to_translate:
            try:
                translated_texts.append(translate_text(text, target_language))
            except Exception:
                translated_texts.append(text)

    # Reconstruct the translated report dict
    translated_report = dict(report)
    for index, translated in enumerate(translated_texts):
        if index >= len(mapping):
            break
        m_type, path_info, item_idx = mapping[index]
        if m_type == 'string':
            key = path_info
            translated_report[key] = translated
        elif m_type == 'list':
            key = path_info
            # Copy the list if not copied yet to avoid modifying the original report in place
            if translated_report[key] is report[key]:
                translated_report[key] = list(report[key])
            translated_report[key][item_idx] = translated
        elif m_type == 'dict_string':
            key, list_idx, dict_key = path_info
            if translated_report[key] is report[key]:
                translated_report[key] = [dict(d) if isinstance(d, dict) else d for d in report[key]]
            translated_report[key][list_idx][dict_key] = translated
        elif m_type == 'dict_list':
            key, list_idx, dict_key, sub_idx = path_info
            if translated_report[key] is report[key]:
                translated_report[key] = [dict(d) if isinstance(d, dict) else d for d in report[key]]
            # Make sure we don't modify the sublist in place if it's shared
            if translated_report[key][list_idx][dict_key] is report[key][list_idx][dict_key]:
                translated_report[key][list_idx][dict_key] = list(report[key][list_idx][dict_key])
            translated_report[key][list_idx][dict_key][sub_idx] = translated

    return translated_report
