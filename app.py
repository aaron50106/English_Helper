"""
英文單字訓練系統 - Flask 網頁版後端
將原本 PyQt5 桌面版的五大模組改以網頁 REST API 提供，
前端（templates/static）透過 fetch 呼叫這些 API 進行操作。

模組：
  1. 單字訓練     /api/vocab/*
  2. 歷屆題目練習 /api/exam/*
  3. 隨機測驗     /api/quiz/*
  4. 新增單字     /api/lookup, /api/custom/*
  5. 測驗紀錄     /api/records
"""

import random
from datetime import datetime

from flask import Flask, render_template, request, jsonify

from data_manager import get_data_manager
from training_engine import get_training_engine
from utils.input_new_vocabulary import VocabularyLookupService
from utils.app_logger import get_app_logger


LOGGER = get_app_logger("english_helper.web")

app = Flask(__name__)

# 後端單例（單機個人工具，全域共用狀態即可）
data_manager = get_data_manager()
data_manager.load_exam_questions()
engine = get_training_engine()
lookup_service = VocabularyLookupService()

# 伺服器端暫存狀態
_vocab_current = None          # 最近一題單字訓練（含答案，不回傳前端）
_exam_session = None           # 歷屆練習：{questions, index, correct, answered, year, type}


# ==================== 首頁 ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== 模組1：單字訓練 ====================

@app.route("/api/vocab/question", methods=["POST"])
def vocab_question():
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "mixed")
    question = engine.get_vocabulary_training_question(mode=mode)
    if not question:
        return jsonify({"ok": False, "message": "詞庫為空，無法出題"}), 400

    global _vocab_current
    _vocab_current = question
    LOGGER.info("Web vocab question mode=%s", question.get("mode"))
    return jsonify({
        "ok": True,
        "prompt": question["prompt"],
        "hint": question.get("hint", ""),
        "options": question["options"],
        "mode": question.get("mode"),
    })


@app.route("/api/vocab/answer", methods=["POST"])
def vocab_answer():
    global _vocab_current
    if not _vocab_current:
        return jsonify({"ok": False, "message": "尚未有題目，請先開始訓練"}), 400

    payload = request.get_json(silent=True) or {}
    option = (payload.get("option", "") or "").upper()
    correct_option = _vocab_current["correct_option"]
    is_correct = option == correct_option.upper()

    data_manager.record_daily_vocab_answer(is_correct)
    LOGGER.info("Web vocab answer option=%s correct=%s", option, is_correct)

    return jsonify({
        "ok": True,
        "is_correct": is_correct,
        "correct_option": correct_option,
        "correct_answer": _vocab_current.get("correct_answer", ""),
        "prompt": _vocab_current.get("prompt", ""),
        "mode": _vocab_current.get("mode"),
        "stats": data_manager.get_daily_vocab_stats(),
    })


@app.route("/api/vocab/stats")
def vocab_stats():
    return jsonify(data_manager.get_daily_vocab_stats())


# ==================== 模組2：歷屆題目練習 ====================

def _exam_question_payload():
    session = _exam_session
    total = len(session["questions"])
    index = session["index"]

    if index >= total:
        accuracy = session["correct"] / total * 100 if total else 0
        return {
            "finished": True,
            "correct": session["correct"],
            "total": total,
            "accuracy": accuracy,
        }

    question = session["questions"][index]
    question_type = question.get("question_type") or question.get("type") or "未知題型"
    raw_options = question.get("options", {})
    if isinstance(raw_options, dict):
        options = {
            "A": raw_options.get("A", ""),
            "B": raw_options.get("B", ""),
            "C": raw_options.get("C", ""),
            "D": raw_options.get("D", ""),
        }
    else:
        options = {chr(65 + i): (raw_options[i] if i < len(raw_options) else "") for i in range(4)}

    return {
        "finished": False,
        "year": question.get("year", "未知"),
        "question_type": question_type,
        "prompt": question.get("prompt") or question.get("question", ""),
        "options": options,
        "index": index,
        "answered": session["answered"],
        "correct": session["correct"],
        "total": total,
    }


@app.route("/api/exam/start", methods=["POST"])
def exam_start():
    payload = request.get_json(silent=True) or {}
    try:
        year = int(payload.get("year"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "年份無效"}), 400
    q_type = payload.get("type")
    random_order = bool(payload.get("random_order", True))

    questions = data_manager.filter_exam_questions(year=year, question_type=q_type)
    if not questions:
        return jsonify({"ok": False, "message": "沒有符合條件的題目"}), 404

    questions = list(questions)
    if random_order:
        random.shuffle(questions)

    global _exam_session
    _exam_session = {
        "questions": questions,
        "index": 0,
        "correct": 0,
        "answered": 0,
        "year": year,
        "type": q_type,
    }
    LOGGER.info("Web exam start year=%s type=%s total=%s", year, q_type, len(questions))
    return jsonify({"ok": True, **_exam_question_payload()})


@app.route("/api/exam/answer", methods=["POST"])
def exam_answer():
    session = _exam_session
    if not session or session["index"] >= len(session["questions"]):
        return jsonify({"ok": False, "message": "沒有進行中的練習"}), 400

    payload = request.get_json(silent=True) or {}
    option = (payload.get("option", "") or "").upper()
    question = session["questions"][session["index"]]
    correct_option = question.get("correct_option")
    has_answer = correct_option in ["A", "B", "C", "D"]
    is_correct = has_answer and option == correct_option

    session["answered"] += 1
    if is_correct:
        session["correct"] += 1

    LOGGER.info("Web exam answer option=%s correct=%s", option, is_correct)
    return jsonify({
        "ok": True,
        "is_correct": is_correct,
        "has_answer": has_answer,
        "correct_option": correct_option,
        "correct": session["correct"],
        "answered": session["answered"],
        "total": len(session["questions"]),
    })


@app.route("/api/exam/next", methods=["POST"])
def exam_next():
    session = _exam_session
    if not session:
        return jsonify({"ok": False, "message": "沒有進行中的練習"}), 400

    session["index"] += 1
    result = _exam_question_payload()

    if result.get("finished"):
        total = result["total"]
        data_manager.add_training_record({
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "record_type": "歷屆練習",
            "item_name": f"{session['year']} 年 {session['type']}",
            "total_questions": total,
            "correct_answers": session["correct"],
            "accuracy": result["accuracy"],
            "spent_time": 0,
        })
        LOGGER.info("Web exam finished total=%s correct=%s", total, session["correct"])

    return jsonify({"ok": True, **result})


# ==================== 模組3：隨機測驗 ====================

def _quiz_current_payload():
    question = engine.get_current_question()
    stats = engine.get_session_statistics()
    if not question:
        return {"finished": True, "stats": stats}

    return {
        "finished": False,
        "prompt": question["prompt"],
        "options": question["options"],
        "answered": stats.get("answered", 0),
        "total": stats.get("total_questions", 0),
        "correct": stats.get("correct", 0),
        "accuracy": stats.get("accuracy", 0),
    }


@app.route("/api/quiz/start", methods=["POST"])
def quiz_start():
    payload = request.get_json(silent=True) or {}
    try:
        count = int(payload.get("count", 10))
    except (TypeError, ValueError):
        count = 10
    include_vocab = bool(payload.get("include_vocab", True))
    include_exam = bool(payload.get("include_exam", True))

    if not include_vocab and not include_exam:
        return jsonify({"ok": False, "message": "至少選擇一種題型"}), 400

    engine.start_random_quiz(
        question_count=count,
        include_vocab=include_vocab,
        include_exam=include_exam,
        seed=None,
    )
    LOGGER.info("Web quiz start count=%s vocab=%s exam=%s", count, include_vocab, include_exam)
    return jsonify({"ok": True, **_quiz_current_payload()})


@app.route("/api/quiz/answer", methods=["POST"])
def quiz_answer():
    payload = request.get_json(silent=True) or {}
    option = payload.get("option", "")

    current = engine.get_current_question()
    if not current:
        return jsonify({"ok": False, "message": "沒有進行中的測驗"}), 400

    is_correct, _ = engine.submit_answer(option)
    correct_option = current.get("correct_option")
    stats = engine.get_session_statistics()

    LOGGER.info("Web quiz answer option=%s correct=%s", option, is_correct)
    return jsonify({
        "ok": True,
        "is_correct": is_correct,
        "correct_option": correct_option,
        "has_answer": correct_option in ["A", "B", "C", "D"],
        "correct_answer": current.get("correct_answer", ""),
        "mode": current.get("mode"),
        "type": current.get("type"),
        "prompt": current.get("prompt"),
        "stats": stats,
        "finished": engine.get_current_question() is None,
    })


@app.route("/api/quiz/next", methods=["POST"])
def quiz_next():
    return jsonify({"ok": True, **_quiz_current_payload()})


@app.route("/api/quiz/end", methods=["POST"])
def quiz_end():
    record = engine.end_session()
    LOGGER.info("Web quiz end total=%s", record.get("total_questions"))
    return jsonify({"ok": True, "record": record})


@app.route("/api/quiz/reset", methods=["POST"])
def quiz_reset():
    engine.reset_session()
    return jsonify({"ok": True})


# ==================== 模組4：新增單字 / 自訂詞庫 ====================

@app.route("/api/lookup", methods=["POST"])
def lookup():
    payload = request.get_json(silent=True) or {}
    word = payload.get("word", "")
    try:
        result = lookup_service.lookup_word(word)
    except Exception as err:
        LOGGER.exception("Web lookup error word=%s err=%s", word, err)
        result = {"success": False, "error": "查詢流程發生未預期錯誤"}
    return jsonify(result)


@app.route("/api/custom")
def custom_list():
    return jsonify({"words": data_manager.get_custom_vocabulary()})


@app.route("/api/custom/add", methods=["POST"])
def custom_add():
    payload = request.get_json(silent=True) or {}
    english = (payload.get("english", "") or "").strip().lower()
    chinese = (payload.get("chinese", "") or "").strip()
    pos = (payload.get("pos", "") or "").strip()

    if not english:
        return jsonify({"ok": False, "message": "英文不可為空"}), 400
    if not chinese:
        return jsonify({"ok": False, "message": "中文翻譯不可為空"}), 400

    all_vocab = data_manager.get_all_vocabulary()
    if any((w.get("english", "").strip().lower() == english) for w in all_vocab):
        return jsonify({"ok": False, "message": "此單字已存在詞庫中"}), 409

    data_manager.add_custom_word(english=english, chinese=chinese, pos=pos)
    LOGGER.info("Web custom add word=%s", english)
    return jsonify({"ok": True, "message": f"已加入自訂詞庫：{english}"})


@app.route("/api/custom/save", methods=["POST"])
def custom_save():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows", [])

    seen = set()
    core = {w.get("english", "").strip().lower() for w in data_manager.get_vocabulary()}
    cleaned = []

    for i, row in enumerate(rows):
        english = (row.get("english", "") or "").strip().lower()
        chinese = (row.get("chinese", "") or "").strip()
        pos = (row.get("part_of_speech", row.get("pos", "")) or "").strip()

        if not english:
            return jsonify({"ok": False, "message": f"第 {i + 1} 列英文不可為空"}), 400
        if not chinese:
            return jsonify({"ok": False, "message": f"第 {i + 1} 列中文不可為空"}), 400
        if english in seen:
            return jsonify({"ok": False, "message": f"第 {i + 1} 列英文重複：{english}"}), 400
        if english in core:
            return jsonify({"ok": False, "message": f"第 {i + 1} 列英文已存在於核心詞庫：{english}"}), 400

        seen.add(english)
        cleaned.append({"english": english, "chinese": chinese, "part_of_speech": pos})

    data_manager.replace_custom_vocabulary(cleaned)
    LOGGER.info("Web custom save count=%s", len(cleaned))
    return jsonify({"ok": True, "message": "自訂詞庫已更新"})


@app.route("/api/custom/delete", methods=["POST"])
def custom_delete():
    payload = request.get_json(silent=True) or {}
    try:
        index = int(payload.get("index", -1))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "索引無效"}), 400

    data_manager.delete_custom_word(index)
    LOGGER.info("Web custom delete index=%s", index)
    return jsonify({"ok": True})


# ==================== 模組5：測驗紀錄 ====================

@app.route("/api/records")
def records():
    record_type = request.args.get("type", "全部紀錄")
    normalized = [
        data_manager.normalize_training_record(record)
        for record in data_manager.get_training_records()
    ]
    if record_type != "全部紀錄":
        normalized = [r for r in normalized if r["record_type"] == record_type]

    return jsonify({"records": normalized, "count": len(normalized)})


if __name__ == "__main__":
    LOGGER.info("Starting English Helper web server on http://127.0.0.1:5000")
    app.run(host="0.0.0.1", port=5000, debug=False, threaded=True)
