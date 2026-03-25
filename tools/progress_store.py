"""
progress_store.py — Read/write user progress to .tmp/progress.json.
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
PROGRESS_FILE = BASE_DIR / ".tmp" / "progress.json"


def _load() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"modules": {}}


def _save(data: dict) -> None:
    PROGRESS_FILE.parent.mkdir(exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_progress() -> dict:
    return _load()


def mark_lesson_complete(lesson_id: str, module_id: str) -> None:
    data = _load()
    mod = data["modules"].setdefault(module_id, {
        "lessons_completed": [],
        "quiz_score": None,
        "quiz_passed": False,
        "exercise_submitted": False,
        "exercise_feedback": None,
        "module_completed": False,
    })
    if lesson_id not in mod["lessons_completed"]:
        mod["lessons_completed"].append(lesson_id)
    _save(data)


def save_quiz_result(module_id: str, score: int, total: int, passing_score: int) -> None:
    data = _load()
    mod = data["modules"].setdefault(module_id, {
        "lessons_completed": [],
        "quiz_score": None,
        "quiz_passed": False,
        "exercise_submitted": False,
        "exercise_feedback": None,
        "module_completed": False,
    })
    mod["quiz_score"] = score
    mod["quiz_total"] = total
    mod["quiz_passed"] = score >= passing_score
    _save(data)


def save_exercise_feedback(module_id: str, feedback: dict) -> None:
    data = _load()
    mod = data["modules"].setdefault(module_id, {
        "lessons_completed": [],
        "quiz_score": None,
        "quiz_passed": False,
        "exercise_submitted": False,
        "exercise_feedback": None,
        "module_completed": False,
    })
    mod["exercise_submitted"] = True
    mod["exercise_feedback"] = feedback
    # Mark module complete if quiz also passed
    if mod.get("quiz_passed"):
        mod["module_completed"] = True
    _save(data)


def get_module_status(module_id: str) -> dict:
    data = _load()
    return data["modules"].get(module_id, {
        "lessons_completed": [],
        "quiz_score": None,
        "quiz_passed": False,
        "exercise_submitted": False,
        "module_completed": False,
    })


def is_quiz_unlocked(module_id: str, total_lessons: int) -> bool:
    """Quiz unlocks after all lessons in a module are viewed."""
    status = get_module_status(module_id)
    return len(status.get("lessons_completed", [])) >= total_lessons


def is_exercise_unlocked(module_id: str) -> bool:
    """Exercise unlocks after quiz is passed."""
    status = get_module_status(module_id)
    return status.get("quiz_passed", False)
