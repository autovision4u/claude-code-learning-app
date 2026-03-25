"""
claude_client.py — Anthropic SDK wrapper for the Hebrew Claude Code learning app.

Three call modes:
  simple_call()      — single request/response
  streaming_call()   — yields text chunks for SSE streaming
  evaluate_exercise() — sends exercise + system prompt, returns structured dict
"""

import os
import json
from pathlib import Path
from typing import Generator

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-5")
BASE_DIR = Path(__file__).parent.parent


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in .env")
    return anthropic.Anthropic(api_key=api_key)


def simple_call(system: str, user: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """Single synchronous call. Returns the full response text."""
    try:
        client = _get_client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        return f"שגיאה בקריאה ל-API: {str(e)}"
    except ValueError as e:
        return f"שגיאת הגדרה: {str(e)}"


def streaming_call(
    system: str, user: str, temperature: float = 0.7
) -> Generator[str, None, None]:
    """Streaming call. Yields text chunks as they arrive."""
    try:
        client = _get_client()
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.APIError as e:
        yield f"שגיאה בקריאה ל-API: {str(e)}"
    except ValueError as e:
        yield f"שגיאת הגדרה: {str(e)}"


def evaluate_exercise(system_prompt_path: str, user_input: str) -> dict:
    """
    Evaluates a user's exercise. Loads the system prompt from file,
    calls Claude, and parses the expected JSON response.

    Returns dict with keys: worked_well, improve, improved_example, error (if any)
    """
    prompt_file = BASE_DIR / "data" / "system_prompts" / system_prompt_path
    try:
        system_prompt = prompt_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"error": f"קובץ הנחיות לא נמצא: {system_prompt_path}"}

    try:
        client = _get_client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}],
        )
        raw = message.content[0].text.strip()

        # The system prompt instructs Claude to return JSON inside ```json ... ```
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return the raw text in a structured way
        return {
            "worked_well": "ראה משוב מטה",
            "improve": raw if "raw" in dir() else "לא ניתן לפרש את התגובה",
            "improved_example": "",
        }
    except anthropic.APIError as e:
        return {"error": f"שגיאה בקריאה ל-API: {str(e)}"}
    except ValueError as e:
        return {"error": f"שגיאת הגדרה: {str(e)}"}


def multi_turn_call(system: str, messages: list, temperature: float = 0.7) -> str:
    """Multi-turn conversation call. messages is a list of {role, content} dicts."""
    try:
        client = _get_client()
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        return message.content[0].text
    except anthropic.APIError as e:
        return f"שגיאה בקריאה ל-API: {str(e)}"
    except ValueError as e:
        return f"שגיאת הגדרה: {str(e)}"


def get_quiz_hint(question_text: str, user_answer: str, correct_answer_hint: str) -> str:
    """Returns a Socratic hint for a quiz question — guides without giving the answer."""
    system = (
        "אתה מדריך לימודי ידידותי שעוזר לתלמידים ללמוד על Claude Code. "
        "כאשר תלמיד טועה בשאלה, תן לו רמז סוקרטי — שאלה שמכוונת אותו לחשוב, "
        "אבל אל תגלה את התשובה הנכונה ישירות. "
        "ענה תמיד בעברית. היה עידודי ותומך."
    )
    user = (
        f"שאלה: {question_text}\n"
        f"תשובת התלמיד: {user_answer}\n"
        f"רמז לכיוון הנכון (אל תגלה זאת): {correct_answer_hint}\n\n"
        "תן רמז קצר שיכוון את התלמיד לתשובה הנכונה."
    )
    return simple_call(system, user, temperature=0.5, max_tokens=256)
