# ============================================================
# handlers/start_handler.py - /start komandasi va asosiy menyu
# ============================================================

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards.reply_keyboards import main_menu_keyboard
from services.json_service import user_exists, save_user

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or "Foydalanuvchi"

    if not user_exists(user_id):
        save_user(user_id, {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
        })
        logger.info(f"Yangi foydalanuvchi: {user_id} ({full_name})")

    await message.answer(
        f"👋 Salom, <b>{full_name}</b>!\n\n"
        "Bu bot sizga ingliz tilini o'rganishga yordam beradi.\n\n"
        "🔽 Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message):
    await message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=main_menu_keyboard(),
    )
