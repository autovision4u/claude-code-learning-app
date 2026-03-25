"""
lesson_loader.py — Load and validate lesson JSON data files.
"""

import json
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).parent.parent
LESSONS_DIR = BASE_DIR / "data" / "lessons"


@lru_cache(maxsize=None)
def load_module(module_id: str) -> dict:
    """Load a module JSON file by module_id. Cached after first load."""
    matches = list(LESSONS_DIR.glob(f"{module_id}_*.json"))
    if not matches:
        raise FileNotFoundError(f"No lesson file found for module_id: {module_id}")
    return json.loads(matches[0].read_text(encoding="utf-8"))


def load_all_modules() -> list[dict]:
    """Load all modules sorted by their 'order' field."""
    modules = []
    for f in LESSONS_DIR.glob("module_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        modules.append(data)
    return sorted(modules, key=lambda m: m.get("order", 99))


def get_lesson(lesson_id: str) -> tuple[dict, dict]:
    """
    Find a lesson by lesson_id across all modules.
    Returns (module, lesson) tuple.
    """
    for module in load_all_modules():
        for lesson in module.get("lessons", []):
            if lesson["lesson_id"] == lesson_id:
                return module, lesson
    raise KeyError(f"Lesson not found: {lesson_id}")


def get_module_lessons(module_id: str) -> list[dict]:
    """Return ordered list of lessons for a module."""
    module = load_module(module_id)
    return module.get("lessons", [])


def get_quiz(module_id: str) -> dict:
    """Return the quiz dict for a module."""
    module = load_module(module_id)
    return module.get("quiz", {})


def get_exercise(module_id: str) -> dict:
    """Return the exercise dict for a module."""
    module = load_module(module_id)
    return module.get("exercise", {})
