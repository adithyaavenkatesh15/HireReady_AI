"""
memory.py

Handles persistent local memory for HireReady AI, following the same
simple JSON-file approach used in BOOKS_AGENT.

Stores:
- Conversation history
- Selected language
- Selected job role
- Previous analysis reports
"""

import json
import os

from config import MEMORY_FILE

DEFAULT_MEMORY = {
    "conversation": [],
    "selected_language": "English",
    "selected_job_role": "",
    "previous_reports": [],
}


def load_memory() -> dict:
    """
    Load memory from disk. If the file does not exist, is corrupted, or
    uses an old incompatible format, return a fresh default memory
    structure.
    """
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_MEMORY)

        if not isinstance(data, dict):
            return dict(DEFAULT_MEMORY)

        # Backward compatibility: ensure all expected keys exist
        memory = dict(DEFAULT_MEMORY)
        for key, default_value in DEFAULT_MEMORY.items():
            if key in data:
                memory[key] = data[key]
            else:
                memory[key] = default_value

        return memory

    return dict(DEFAULT_MEMORY)


def save_memory(memory: dict) -> None:
    """
    Persist the given memory dictionary to disk as JSON.
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def add_conversation_turn(user_message: str, assistant_message: str) -> None:
    """
    Append a single user/assistant exchange to conversation history.
    """
    memory = load_memory()
    memory["conversation"].append({"role": "user", "content": user_message})
    memory["conversation"].append({"role": "assistant", "content": assistant_message})
    save_memory(memory)


def set_selected_language(language: str) -> None:
    memory = load_memory()
    memory["selected_language"] = language
    save_memory(memory)


def set_selected_job_role(job_role: str) -> None:
    memory = load_memory()
    memory["selected_job_role"] = job_role
    save_memory(memory)


def add_report(report: dict) -> None:
    """
    Store a completed analysis report in memory history.
    """
    memory = load_memory()
    memory["previous_reports"].append(report)
    save_memory(memory)


def get_previous_reports() -> list:
    return load_memory().get("previous_reports", [])


def clear_memory() -> None:
    """
    Reset memory back to defaults (used by a "Reset" button in the UI).
    """
    save_memory(dict(DEFAULT_MEMORY))
