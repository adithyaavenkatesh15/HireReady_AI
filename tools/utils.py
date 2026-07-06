"""
tools/utils.py

Small shared helper functions used across multiple tools and agents,
including the shared OpenRouter LLM client used by every agent.
"""

import json
import re

import requests

from config import OPENROUTER_API_KEY, OPENROUTER_URL, OPENROUTER_MODEL


class LLMError(Exception):
    """Raised when a call to the LLM provider fails."""


def call_llm(system_prompt: str, user_message: str, temperature: float = 0.4) -> str:
    """
    Call the OpenRouter chat completions endpoint with a system prompt
    and a single user message, returning the raw text response.

    All six agents share this single function so LLM-calling logic
    never needs to be duplicated across agent files.

    Args:
        system_prompt: The agent-specific system prompt (from prompts/*.py).
        user_message: The task-specific input (e.g. resume JSON + job description).
        temperature: Sampling temperature for the LLM call.

    Returns:
        str: Raw text content returned by the model.

    Raises:
        LLMError: If the API key is missing or the request fails.
    """
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set. Please configure it in .env.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as exc:
        raise LLMError(f"LLM request failed: {exc}") from exc
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Unexpected LLM response format: {exc}") from exc


def safe_json_parse(raw_text: str) -> dict:
    """
    Safely parse a JSON object out of an LLM response.

    LLMs occasionally wrap JSON in markdown code fences or add stray
    text before/after the JSON object. This function strips fences and
    extracts the first valid JSON object it can find.

    Args:
        raw_text: The raw text returned by the LLM.

    Returns:
        dict: Parsed JSON as a Python dictionary. Returns an empty dict
        if parsing fails.
    """
    if not raw_text:
        return {}

    cleaned = raw_text.strip()

    # Remove markdown code fences if present
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract the first {...} block
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    return {}


def truncate_text(text: str, max_chars: int = 8000) -> str:
    """
    Truncate long resume text so it stays within reasonable LLM context
    limits, keeping the beginning of the document (most resumes front-load
    the most important information).
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Content truncated due to length...]"


def clean_whitespace(text: str) -> str:
    """
    Collapse repeated blank lines and trim trailing whitespace from
    extracted PDF text.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned_lines = []
    blank_streak = 0

    for line in lines:
        if line.strip() == "":
            blank_streak += 1
            if blank_streak > 1:
                continue
        else:
            blank_streak = 0
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
