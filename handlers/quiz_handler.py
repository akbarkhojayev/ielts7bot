import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from keyboards.inline_keyboards import quiz_options_keyboard
from services.json_service import (
    get_all_quizzes,
    get_quiz_by_index,
    get_quiz_count,
    add_quizzes,
    get_user_progress,
    save_user_progress,
    record_quiz_answer,
    increment_quiz_index,
)
from services.groq_service import generate_quiz_questions
from config import QUIZ_REFILL_THRESHOLD

logger = logging.getLogger(__name__)
router = Router()


async def ensure_quizzes_available() -> bool:
    count = get_quiz_count()
    if count < QUIZ_REFILL_THRESHOLD:
        logger.info("Savollar kam, Groq API dan yangilari olinmoqda...")
        new_quizzes = await generate_quiz_questions()
        if new_quizzes:
            add_quizzes(new_quizzes)
            logger.info(f"{len(new_quizzes)} ta yangi savol qo'shildi")
            return True
        else:
            logger.error("Groq API dan savol olishda xato")
            return False
    return True


async def send_quiz_question(message_or_query, user_id: int):
    progress = get_user_progress(user_id)
    index = progress.get("current_quiz_index", 0)
    total = get_quiz_count()

    if index >= total:
        logger.info(f"User {user_id} barcha savollarni ishlab chiqdi, yangi savollar olinmoqda")
        new_quizzes = await generate_quiz_questions()
        if new_quizzes:
            add_quizzes(new_quizzes)
            total = get_quiz_count()
        else:
            text = "⚠️ Hozircha yangi savollar yaratilmadi. Biroz kutib qayta urinib ko'ring."
            if isinstance(message_or_query, CallbackQuery):
                await message_or_query.message.answer(text)
            else:
                await message_or_query.answer(text)
            return

    quiz = get_quiz_by_index(index)
    if not quiz:
        text = "⚠️ Savol topilmadi. /start bosib qayta boshlang."
        if isinstance(message_or_query, CallbackQuery):
            await message_or_query.message.answer(text)
        else:
            await message_or_query.answer(text)
        return

    text = (
        f"📝 <b>Savol {index + 1}</b> | Mavzu: <i>{quiz['tense_or_topic']}</i>\n\n"
        f"❓ {quiz['question']}\n\n"
        f"Quyidagi variantlardan birini tanlang:"
    )

    keyboard = quiz_options_keyboard(quiz["options"], index)

    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_query.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "📝 Quiz")
async def quiz_menu_handler(message: Message):
    user_id = message.from_user.id

    available = await ensure_quizzes_available()
    if not available:
        await message.answer(
            "⚠️ AI bilan bog'lanishda muammo yuz berdi. Internet aloqasini tekshiring."
        )
        return

    await message.answer(
        "🎯 Grammar Quiz boshlandi!\n"
        "Har bir savolni diqqat bilan o'qing va to'g'ri variantni tanlang."
    )
    await send_quiz_question(message, user_id)


@router.callback_query(F.data == "next_question")
async def next_question_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    await ensure_quizzes_available()

    await send_quiz_question(callback, user_id)
    await callback.answer()


@router.callback_query(F.data.startswith("show_explanation:"))
async def show_explanation_handler(callback: CallbackQuery):
    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        await callback.answer("Xato callback data")
        return

    question_index = int(parts[1])
    quiz = get_quiz_by_index(question_index)

    if not quiz:
        await callback.answer("Savol topilmadi")
        return

    explanation_text = (
        f"📖 <b>Tushuntirish:</b>\n\n{quiz['explanation']}"
    )

    from keyboards.inline_keyboards import next_question_keyboard
    keyboard = next_question_keyboard()
    await callback.message.answer(explanation_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_answer:"))
async def quiz_answer_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Xato callback data")
        return

    _, question_index_str, selected_option = parts
    question_index = int(question_index_str)

    quiz = get_quiz_by_index(question_index)
    if not quiz:
        await callback.answer("Savol topilmadi")
        return

    progress = get_user_progress(user_id)
    current_index = progress.get("current_quiz_index", 0)

    if question_index != current_index:
        await callback.answer("Bu savolga allaqachon javob berdingiz!", show_alert=True)
        return

    is_correct = selected_option == quiz["correct_answer"]

    record_quiz_answer(user_id, is_correct)
    new_index = increment_quiz_index(user_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if is_correct:
        result_text = (
            f"✅ <b>To'g'ri!</b> Siz tanlagan: <code>{selected_option}</code>"
        )
        from keyboards.inline_keyboards import show_explanation_or_next_keyboard
        keyboard = show_explanation_or_next_keyboard(question_index)
        await callback.message.answer(result_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        result_text = (
            f"❌ <b>Noto'g'ri!</b> Siz tanlagan: <code>{selected_option}</code>\n"
            f"✅ <b>To'g'ri javob:</b> <code>{quiz['correct_answer']}</code>"
        )
        from keyboards.inline_keyboards import show_explanation_or_next_keyboard
        keyboard = show_explanation_or_next_keyboard(question_index)
        await callback.message.answer(result_text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()

    await ensure_quizzes_available()
