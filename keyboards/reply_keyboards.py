from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Quiz"),
                KeyboardButton(text="📚 Vocabulary"),
            ]
        ],
        resize_keyboard=True,
        persistent=True,
    )


def vocabulary_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ So'z qo'shish"),
                KeyboardButton(text="▶️ Boshlash"),
            ],
            [
                KeyboardButton(text="🔙 Asosiy menyu"),
            ],
        ],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
