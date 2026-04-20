import json
import os
import logging
from config import DATA_DIR, USERS_FILE, QUIZZES_FILE, USER_PROGRESS_FILE, VOCABULARY_FILE

logger = logging.getLogger(__name__)


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

    defaults = {
        USERS_FILE: {},
        QUIZZES_FILE: [],
        USER_PROGRESS_FILE: {},
        VOCABULARY_FILE: [],
    }

    for filepath, default_value in defaults.items():
        if not os.path.exists(filepath):
            _write_json(filepath, default_value)
            logger.info(f"Yaratildi: {filepath}")


def _read_json(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"JSON o'qishda xato ({filepath}): {e}")
        return None


def _write_json(filepath: str, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON yozishda xato ({filepath}): {e}")
        return False


def get_all_users() -> dict:
    return _read_json(USERS_FILE) or {}


def get_user(user_id: int) -> dict | None:
    users = get_all_users()
    return users.get(str(user_id))


def save_user(user_id: int, data: dict) -> bool:
    users = get_all_users()
    users[str(user_id)] = data
    return _write_json(USERS_FILE, users)


def user_exists(user_id: int) -> bool:
    return get_user(user_id) is not None


def get_all_quizzes() -> list:
    return _read_json(QUIZZES_FILE) or []


def get_quiz_by_index(index: int) -> dict | None:
    quizzes = get_all_quizzes()
    if 0 <= index < len(quizzes):
        return quizzes[index]
    return None


def get_quiz_count() -> int:
    return len(get_all_quizzes())


def add_quizzes(new_quizzes: list) -> bool:
    existing = get_all_quizzes()
    existing.extend(new_quizzes)
    return _write_json(QUIZZES_FILE, existing)


def replace_quizzes(quizzes: list) -> bool:
    return _write_json(QUIZZES_FILE, quizzes)


def get_all_progress() -> dict:
    return _read_json(USER_PROGRESS_FILE) or {}


def get_user_progress(user_id: int) -> dict:
    progress = get_all_progress()
    return progress.get(str(user_id), {
        "current_quiz_index": 0,
        "correct_answers": 0,
        "total_answered": 0,
    })


def save_user_progress(user_id: int, progress: dict) -> bool:
    all_progress = get_all_progress()
    all_progress[str(user_id)] = progress
    return _write_json(USER_PROGRESS_FILE, all_progress)


def reset_user_quiz_progress(user_id: int) -> bool:
    progress = get_user_progress(user_id)
    progress["current_quiz_index"] = 0
    progress["correct_answers"] = 0
    progress["total_answered"] = 0
    return save_user_progress(user_id, progress)


def increment_quiz_index(user_id: int) -> int:
    progress = get_user_progress(user_id)
    progress["current_quiz_index"] = progress.get("current_quiz_index", 0) + 1
    save_user_progress(user_id, progress)
    return progress["current_quiz_index"]


def record_quiz_answer(user_id: int, is_correct: bool):
    progress = get_user_progress(user_id)
    progress["total_answered"] = progress.get("total_answered", 0) + 1
    if is_correct:
        progress["correct_answers"] = progress.get("correct_answers", 0) + 1
    save_user_progress(user_id, progress)


def get_all_vocabulary() -> list:
    return _read_json(VOCABULARY_FILE) or []


def word_exists(english_word: str) -> bool:
    vocab = get_all_vocabulary()
    english_word = english_word.strip().lower()
    return any(w["english"].lower() == english_word for w in vocab)


def add_word(english: str, uzbek: str) -> bool:
    vocab = get_all_vocabulary()
    vocab.append({
        "english": english.strip(),
        "uzbek": uzbek.strip(),
    })
    return _write_json(VOCABULARY_FILE, vocab)


def get_vocabulary_count() -> int:
    return len(get_all_vocabulary())
