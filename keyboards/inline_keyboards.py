# ============================================================
# keyboards/inline_keyboards.py - Inline klaviaturalar
# ============================================================

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def quiz_options_keyboard(options: list[str], question_index: int) -> InlineKeyboardMarkup:
    buttons = []
    for option in options:
        buttons.append([
            InlineKeyboardButton(
                text=option,
                callback_data=f"quiz_answer:{question_index}:{option}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def show_explanation_or_next_keyboard(question_index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📖 Tushuntirish",
                callback_data=f"show_explanation:{question_index}",
            )],
            [InlineKeyboardButton(
                text="➡️ Keyingi savol",
                callback_data="next_question",
            )]
        ]
    )


def vocabulary_quiz_keyboard(options: list[str], correct: str, question_index: int) -> InlineKeyboardMarkup:
    buttons = []
    for option in options:
        buttons.append([
            InlineKeyboardButton(
                text=option,
                callback_data=f"vocab_answer:{question_index}:{option}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def next_question_keyboard(label: str = "➡️ Keyingi savol") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data="next_question")]
        ]
    )
