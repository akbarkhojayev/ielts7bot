import logging
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply_keyboards import vocabulary_menu_keyboard, main_menu_keyboard
from keyboards.inline_keyboards import vocabulary_quiz_keyboard
from services.json_service import (
    get_all_vocabulary,
    word_exists,
    add_word,
    get_vocabulary_count,
)

logger = logging.getLogger(__name__)
router = Router()

class VocabStates(StatesGroup):
    waiting_for_word = State()
    vocab_quiz_active = State()


@router.message(F.text == "📚 Vocabulary")
async def vocabulary_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📚 <b>Vocabulary bo'limi</b>\n\n"
        "Bu bo'limda so'z qo'shishingiz va o'rganishingiz mumkin.",
        reply_markup=vocabulary_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "➕ So'z qo'shish")
async def add_word_handler(message: Message, state: FSMContext):
    await state.set_state(VocabStates.waiting_for_word)
    await message.answer(
        "✍️ Yangi so'zni quyidagi formatda kiriting:\n\n"
        "<code>inglizcha - o'zbekcha</code>\n\n"
        "📌 <b>Misol:</b> <code>apple - olma</code>\n\n"
        "Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(VocabStates.waiting_for_word)
async def receive_new_word(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❎ Bekor qilindi.",
            reply_markup=vocabulary_menu_keyboard(),
        )
        return

    if " - " not in text:
        await message.answer(
            "⚠️ <b>Noto'g'ri format!</b>\n\n"
            "Iltimos, quyidagi formatda kiriting:\n"
            "<code>inglizcha - o'zbekcha</code>\n\n"
            "📌 <b>Misol:</b> <code>apple - olma</code>",
            parse_mode="HTML",
        )
        return

    parts = text.split(" - ", 1)
    if len(parts) != 2:
        await message.answer("⚠️ Format noto'g'ri. Misol: <code>apple - olma</code>", parse_mode="HTML")
        return

    english_word = parts[0].strip()
    uzbek_word = parts[1].strip()

    if not english_word or not uzbek_word:
        await message.answer("⚠️ So'z yoki tarjima bo'sh bo'lmasin.")
        return

    if word_exists(english_word):
        await message.answer(
            f"⚠️ <b>'{english_word}'</b> so'zi allaqachon bazada mavjud!",
            parse_mode="HTML",
        )
        await state.clear()
        await message.answer("Boshqa so'z kiriting yoki menyuga qayting.", reply_markup=vocabulary_menu_keyboard())
        return

    success = add_word(english_word, uzbek_word)

    if success:
        await message.answer(
            f"✅ <b>So'z qo'shildi!</b>\n\n"
            f"🇬🇧 {english_word} → 🇺🇿 {uzbek_word}\n\n"
            f"📊 Jami so'zlar: <b>{get_vocabulary_count()}</b>",
            reply_markup=vocabulary_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "❌ So'z saqlanmadi. Iltimos, qayta urinib ko'ring.",
            reply_markup=vocabulary_menu_keyboard(),
        )

    await state.clear()


def generate_vocab_question(vocab_list: list, index: int) -> dict | None:
    if not vocab_list or index >= len(vocab_list):
        return None

    shuffled = vocab_list[:]

    correct_entry = vocab_list[index]

    if index % 2 == 0:
        question_word = correct_entry["english"]
        correct_answer = correct_entry["uzbek"]
        question_text = f"🇬🇧 <b>{question_word}</b>\n\nQaysi biri to'g'ri tarjima?"
        wrong_options = [w["uzbek"] for w in vocab_list if w["uzbek"] != correct_answer]
    else:
        question_word = correct_entry["uzbek"]
        correct_answer = correct_entry["english"]
        question_text = f"🇺🇿 <b>{question_word}</b>\n\nQaysi biri to'g'ri tarjima?"
        wrong_options = [w["english"] for w in vocab_list if w["english"] != correct_answer]

    if len(wrong_options) < 2:
        return None

    wrong_sample = random.sample(wrong_options, min(2, len(wrong_options)))
    all_options = [correct_answer] + wrong_sample
    random.shuffle(all_options)

    return {
        "question_text": question_text,
        "options": all_options,
        "correct_answer": correct_answer,
        "index": index,
    }


async def send_vocab_question(target, user_id: int, state: FSMContext):
    vocab_list = get_all_vocabulary()

    if len(vocab_list) < 3:
        text = (
            "⚠️ Quiz boshlash uchun kamita <b>3 ta so'z</b> bo'lishi kerak.\n"
            "Avval so'z qo'shing!"
        )
        if isinstance(target, CallbackQuery):
            await target.message.answer(text, parse_mode="HTML", reply_markup=vocabulary_menu_keyboard())
        else:
            await target.answer(text, parse_mode="HTML", reply_markup=vocabulary_menu_keyboard())
        await state.clear()
        return

    data = await state.get_data()
    current_index = data.get("vocab_index", 0)
    vocab_indices = data.get("vocab_indices", [])

    if current_index >= len(vocab_indices):
        total = data.get("vocab_total", len(vocab_list))
        correct = data.get("vocab_correct", 0)

        finish_text = (
            f"🎉 <b>Vocabulary quiz yakunlandi!</b>\n\n"
            f"📊 Natija: <b>{correct}/{total}</b>\n"
            f"{'🏆 Ajoyib!' if correct == total else '💪 Davom eting!'}"
        )

        if isinstance(target, CallbackQuery):
            await target.message.answer(finish_text, parse_mode="HTML", reply_markup=vocabulary_menu_keyboard())
        else:
            await target.answer(finish_text, parse_mode="HTML", reply_markup=vocabulary_menu_keyboard())
        await state.clear()
        return

    actual_index = vocab_indices[current_index]
    question = generate_vocab_question(vocab_list, actual_index)

    if not question:
        if isinstance(target, CallbackQuery):
            await target.message.answer(
                "⚠️ Savol yaratishda xato. Kamita 3 ta so'z qo'shing.",
                reply_markup=vocabulary_menu_keyboard()
            )
        else:
            await target.answer("⚠️ Savol yaratishda xato.", reply_markup=vocabulary_menu_keyboard())
        await state.clear()
        return

    text = (
        f"📚 <b>So'z {current_index + 1}/{len(vocab_list)}</b>\n\n"
        f"{question['question_text']}"
    )

    keyboard = vocabulary_quiz_keyboard(
        question["options"],
        question["correct_answer"],
        current_index,
    )

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")

    await state.update_data(
        vocab_correct_answer=question["correct_answer"],
        vocab_total=len(vocab_list),
    )


@router.message(F.text == "▶️ Boshlash")
async def start_vocab_quiz(message: Message, state: FSMContext):
    vocab_list = get_all_vocabulary()

    if len(vocab_list) < 3:
        await message.answer(
            "⚠️ Quiz boshlash uchun kamita <b>3 ta so'z</b> kerak.\n"
            "Avval '➕ So'z qo'shish' tugmasini bosing!",
            parse_mode="HTML",
        )
        return

    indices = list(range(len(vocab_list)))
    random.shuffle(indices)

    await state.set_state(VocabStates.vocab_quiz_active)
    await state.update_data(
        vocab_index=0,
        vocab_indices=indices,
        vocab_correct=0,
        vocab_total=len(vocab_list),
    )

    await message.answer(
        f"🚀 Vocabulary quiz boshlandi! Jami <b>{len(vocab_list)}</b> ta so'z.",
        parse_mode="HTML",
    )
    await send_vocab_question(message, message.from_user.id, state)


@router.callback_query(VocabStates.vocab_quiz_active, F.data.startswith("vocab_answer:"))
async def vocab_answer_handler(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Xato callback data")
        return

    _, question_index_str, selected_option = parts

    data = await state.get_data()
    correct_answer = data.get("vocab_correct_answer", "")
    current_index = data.get("vocab_index", 0)

    if int(question_index_str) != current_index:
        await callback.answer("Bu savolga allaqachon javob berdingiz!", show_alert=True)
        return

    is_correct = selected_option == correct_answer

    vocab_correct = data.get("vocab_correct", 0)
    if is_correct:
        vocab_correct += 1

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if is_correct:
        result_text = (
            f"✅ <b>To'g'ri!</b>\n"
            f"Siz tanlagan: <code>{selected_option}</code>"
        )
    else:
        result_text = (
            f"❌ <b>Noto'g'ri!</b>\n"
            f"Siz tanlagan: <code>{selected_option}</code>\n"
            f"✅ To'g'ri javob: <code>{correct_answer}</code>"
        )

    await callback.message.answer(result_text, parse_mode="HTML")
    await callback.answer()

    next_index = current_index + 1
    await state.update_data(
        vocab_index=next_index,
        vocab_correct=vocab_correct,
    )

    await send_vocab_question(callback, callback.from_user.id, state)
