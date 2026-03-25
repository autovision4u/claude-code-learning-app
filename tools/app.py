"""
app.py — Flask web server for the Hebrew Claude Code learning app.
Run: python tools/app.py
Then open: http://localhost:5000
"""

import sys
import os
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent))
ROOT_DIR = Path(__file__).parent.parent

from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    Response, stream_with_context
)
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / ".env")

import lesson_loader
import progress_store
import claude_client

app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "templates"),
    static_folder=str(ROOT_DIR / "static"),
)
app.secret_key = os.getenv("FLASK_SECRET", "claude-code-learner-secret")


# ── HOME ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    modules = lesson_loader.load_all_modules()
    progress = progress_store.get_progress()
    return render_template("index.html", modules=modules, progress=progress["modules"])


# ── MODULE / LESSON ──────────────────────────────────────────────────────────

@app.route("/module/<module_id>")
def module_start(module_id):
    """Redirect to the first incomplete lesson in a module."""
    lessons = lesson_loader.get_module_lessons(module_id)
    status = progress_store.get_module_status(module_id)
    completed = status.get("lessons_completed", [])
    for lesson in lessons:
        if lesson["lesson_id"] not in completed:
            return redirect(url_for("lesson", lesson_id=lesson["lesson_id"]))
    # All lessons done — go to quiz
    return redirect(url_for("quiz", module_id=module_id))


@app.route("/lesson/<lesson_id>")
def lesson(lesson_id):
    module, lesson_data = lesson_loader.get_lesson(lesson_id)
    lessons = lesson_loader.get_module_lessons(module["module_id"])
    status = progress_store.get_module_status(module["module_id"])

    # Find prev/next lesson
    lesson_ids = [l["lesson_id"] for l in lessons]
    idx = lesson_ids.index(lesson_id)
    prev_id = lesson_ids[idx - 1] if idx > 0 else None
    next_id = lesson_ids[idx + 1] if idx < len(lesson_ids) - 1 else None

    # Auto-mark as complete on view
    progress_store.mark_lesson_complete(lesson_id, module["module_id"])

    quiz_unlocked = progress_store.is_quiz_unlocked(module["module_id"], len(lessons))

    return render_template(
        "lesson.html",
        module=module,
        lesson=lesson_data,
        lessons=lessons,
        lesson_index=idx,
        prev_id=prev_id,
        next_id=next_id,
        quiz_unlocked=quiz_unlocked,
        status=status,
    )


# ── QUIZ ──────────────────────────────────────────────────────────────────────

@app.route("/quiz/<module_id>")
def quiz(module_id):
    module = lesson_loader.load_module(module_id)
    quiz_data = lesson_loader.get_quiz(module_id)
    lessons = lesson_loader.get_module_lessons(module_id)
    status = progress_store.get_module_status(module_id)

    if not progress_store.is_quiz_unlocked(module_id, len(lessons)):
        return redirect(url_for("module_start", module_id=module_id))

    return render_template("quiz.html", module=module, quiz=quiz_data, status=status)


@app.route("/api/quiz/answer", methods=["POST"])
def quiz_answer():
    data = request.json
    module_id = data["module_id"]
    answers = data["answers"]  # {question_id: selected_option_id}

    quiz_data = lesson_loader.get_quiz(module_id)
    questions = quiz_data["questions"]
    passing_score = quiz_data["passing_score"]

    results = {}
    score = 0
    for q in questions:
        qid = q["question_id"]
        user_ans = answers.get(qid)
        correct = q["correct_answer"]
        is_correct = user_ans == correct
        if is_correct:
            score += 1
        results[qid] = {
            "correct": is_correct,
            "user_answer": user_ans,
            "correct_answer": correct,
            "explanation": q["explanation_he"],
        }

    passed = score >= passing_score
    progress_store.save_quiz_result(module_id, score, len(questions), passing_score)

    return jsonify({
        "score": score,
        "total": len(questions),
        "passed": passed,
        "results": results,
    })


@app.route("/api/quiz/hint", methods=["POST"])
def quiz_hint():
    data = request.json
    module_id = data["module_id"]
    question_id = data["question_id"]
    user_answer = data.get("user_answer", "")

    quiz_data = lesson_loader.get_quiz(module_id)
    question = next((q for q in quiz_data["questions"] if q["question_id"] == question_id), None)
    if not question:
        return jsonify({"hint": "לא נמצאה השאלה"}), 404

    correct_opt = next(o for o in question["options"] if o["id"] == question["correct_answer"])
    hint = claude_client.get_quiz_hint(
        question["question_he"], user_answer, correct_opt["text_he"]
    )
    return jsonify({"hint": hint})


# ── EXERCISE ──────────────────────────────────────────────────────────────────

@app.route("/exercise/<module_id>")
def exercise(module_id):
    module = lesson_loader.load_module(module_id)
    exercise_data = lesson_loader.get_exercise(module_id)
    status = progress_store.get_module_status(module_id)

    if not progress_store.is_exercise_unlocked(module_id):
        return redirect(url_for("quiz", module_id=module_id))

    return render_template("exercise.html", module=module, exercise=exercise_data, status=status)


@app.route("/api/exercise/evaluate", methods=["POST"])
def exercise_evaluate():
    data = request.json
    module_id = data["module_id"]
    user_input = data.get("user_input", "").strip()
    exercise_data = lesson_loader.get_exercise(module_id)

    min_len = exercise_data.get("min_length", 10)
    if len(user_input) < min_len:
        return jsonify({"error": f"התשובה קצרה מדי. נסה לכתוב לפחות {min_len} תווים."})

    system_prompt_file = exercise_data["system_prompt_file"]
    feedback = claude_client.evaluate_exercise(system_prompt_file, user_input)
    progress_store.save_exercise_feedback(module_id, feedback)
    return jsonify(feedback)


# ── LIVE DEMO (streaming SSE) ─────────────────────────────────────────────────

@app.route("/api/demo/stream", methods=["POST"])
def demo_stream():
    data = request.json
    system = data.get("system", "אתה עוזר ידידותי.")
    prompt = data.get("prompt", "שלום!")
    temperature = float(data.get("temperature", 0.8))

    def generate():
        for chunk in claude_client.streaming_call(system, prompt, temperature):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/demo", methods=["POST"])
def demo_simple():
    data = request.json
    system = data.get("system", "אתה עוזר ידידותי.")
    prompt = data.get("prompt", "שלום!")
    temperature = float(data.get("temperature", 0.8))
    result = claude_client.simple_call(system, prompt, temperature)
    return jsonify({"result": result})


# ── PROGRESS ──────────────────────────────────────────────────────────────────

@app.route("/progress")
def progress_page():
    modules = lesson_loader.load_all_modules()
    progress = progress_store.get_progress()
    return render_template("progress.html", modules=modules, progress=progress["modules"])


@app.route("/api/progress")
def api_progress():
    return jsonify(progress_store.get_progress())


# ── SOURCE VIEWER ─────────────────────────────────────────────────────────────

@app.route("/show-source/claude_client")
def show_source():
    source_file = ROOT_DIR / "tools" / "claude_client.py"
    source_code = source_file.read_text(encoding="utf-8")
    return render_template("source_viewer.html", source_code=source_code)


# ── RUN ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n>> App running at: http://localhost:{port}\n")
    app.run(debug=True, port=port, host="0.0.0.0")
