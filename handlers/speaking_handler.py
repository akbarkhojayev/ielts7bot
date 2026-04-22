# ============================================================
# handlers/speaking_handler.py - Speaking bo'limi
# ============================================================

import logging
import json
import httpx
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply_keyboards import main_menu_keyboard
from config import GROQ_API_KEYS, GROQ_MODEL

logger = logging.getLogger(__name__)
router = Router()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class SpeakingStates(StatesGroup):
    waiting_for_text = State()


@router.message(F.text == "🎤 Speaking")
async def speaking_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎤 <b>Speaking bo'limi</b>\n\n"
        "Bu bo'limda siz o'zingiz yozgan gaplarni ingliz tiliga to'g'rilashtirib beramiz.\n\n"
        "✍️ Gapni yozing va biz uni pre-intermediate darajasiga to'g'rilashtiramiz.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(SpeakingStates.waiting_for_text)


@router.message(SpeakingStates.waiting_for_text)
async def receive_speaking_text(message: Message, state: FSMContext):
    user_text = message.text.strip()

    if user_text.lower() == "/cancel":
        await state.clear()
        await message.answer(
            "❎ Bekor qilindi.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if len(user_text) < 5:
        await message.answer(
            "⚠️ Iltimos, kamita 5 ta belgidan ko'p gap yozing.",
            parse_mode="HTML",
        )
        return

    # Show loading message
    loading_msg = await message.answer("⏳ Jarayonda... Iltimos kuting...")

    try:
        refined_text, vocabulary = await refine_text_with_groq(user_text)

        if refined_text:
            response_text = (
                f"📝 <b>Kiriting:</b>\n"
                f"{user_text}\n\n"
                f"✅ <b>Natija:</b>\n"
                f"{refined_text}\n\n"
            )

            if vocabulary:
                response_text += vocabulary

            await loading_msg.delete()
            await message.answer(response_text, parse_mode="HTML")
            
            # Ask for another text
            await message.answer(
                "🎤 Yana bir gap yozishni xohlaysizmi?\n\n"
                "Bekor qilish uchun /cancel yozing.",
                parse_mode="HTML",
            )
        else:
            await loading_msg.delete()
            await message.answer(
                "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring.",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Speaking handler da xato: {e}")
        await loading_msg.delete()
        await message.answer(
            "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()


async def refine_text_with_groq(user_text: str) -> tuple[str | None, str | None]:
    """
    Groq API orqali foydalanuvchining gapini to'g'rilaydi va vocabulary qaytaradi
    Bir nechta API keylar bilan fallback qo'llab-quvvatlaydi
    """
    
    for api_key_index, api_key in enumerate(GROQ_API_KEYS):
        try:
            logger.info(f"Speaking uchun API key #{api_key_index + 1} ishlatilmoqda...")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            prompt = f"""Siz Pre-Intermediate English Teacher va Speaking Coach siz. Sizning vazifangiz foydalanuvchining yozgan gaplarini pre-intermediate darajasiga mos qilib to'g'rilash, ularning asl g'oyasini saqlash va yanada yaxshi tushunchalar bilan rivojlantirish.

FOYDALANUVCHINING YOZGAN MATNI:
"{user_text}"

SIZNING VAZIFALARINGIZ:

1. ASLIY G'OYANI SAQLANG:
   - Foydalanuvchining asl fikrini o'zgartirib yubormang
   - Ularning asosiy xabarini qo'llab-quvvatlang

2. GAPNI TO'G'RILANG VA RIVOJLANTIRING:
   - Pre-intermediate darajadagi grammatik strukturalarni ishlatilsin (Simple Present, Past Simple, Present Continuous, Future Simple, etc.)
   - Gapning ma'nosi o'zgarmasin, lekin yanada aniq va to'liq bo'lsin
   - 1-2 ta yangi fikr yoki tushuncha qo'shing (ularning g'oyasini rivojlantirish uchun)
   - Jami 2-6 ta jumla bo'lsin
   - Sodda va tushunarli so'zlar ishlatilsin
   - Agar kerak bo'lsa, gapning boshida savol qo'shing

3. VOCABULARY TANLANG (KAMITA 3-6 TA SO'Z):
   - To'g'rilangan gapdan eng muhim 3-6 ta so'zni tanlang
   - Faqat pre-intermediate darajadagi so'zlarni tanlang
   - Har bir so'z uchun aniq o'zbekcha tarjima bering
   - Agar kerak bo'lsa, qisqa tushuntirish qo'shing

MISOL:
Kiriting: "I think it is easy to be teacher. Because Teachers should know about topics they teach in advance."

Natija:
{{
    "refined_text": "Is it difficult to be a teacher? I think being a teacher is easy. Teachers just need to know their subject well before they teach it to students. Also, they need to explain topics in a simple way. That is why I think teaching is not a difficult job.",
    "vocabulary": [
        {{"word": "Subject", "translation": "Fan"}},
        {{"word": "Explain", "translation": "Tushuntirmoq"}},
        {{"word": "Simple way", "translation": "Oddiy usul"}},
        {{"word": "Difficult job", "translation": "Qiyin ish"}},
        {{"word": "In advance", "translation": "Oldindan"}}
    ]
}}

MUHIM TALABLAR:
- Asliy g'oyani saqlang va rivojlantiring
- 2-6 ta jumla bo'lsin
- Pre-intermediate grammatik strukturalarni ishlatilsin
- Kamita 3-6 ta so'z vocabulary bo'lsin
- 1-2 ta yangi fikr qo'shing (ularning tushunchalarini rivojlantirish uchun)
- Faqat JSON formatida javob bering - boshqa hech narsa yozmang!
- JSON formatida xato bo'lmasin!"""

            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": """Siz Pre-Intermediate English Teacher va Speaking Coach siz. Foydalanuvchining yozgan gaplarini pre-intermediate darajasiga mos qilib to'g'rilaysiz va rivojlantirasiz.

MUHIM QOIDALAR:
1. Asliy g'oyani SAQLANG - o'zgartirib yubormang
2. 2-6 ta jumla bo'lsin
3. Pre-intermediate grammatik strukturalarni ishlatilsin (Simple Present, Past Simple, Present Continuous, Future Simple, etc.)
4. 1-2 ta yangi fikr yoki tushuncha qo'shing (ularning tushunchalarini rivojlantirish uchun)
5. Kamita 3-6 ta so'z vocabulary bo'lsin
6. Faqat JSON formatida javob bering - boshqa hech narsa yozmang!
7. JSON formatida xato bo'lmasin!
8. Gapning ma'nosi o'zgarmasin, lekin yanada aniq va to'liq bo'lsin""",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0.8,
                "max_tokens": 1500,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
                response.raise_for_status()

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            # Clean up markdown code blocks if present
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

            result = json.loads(raw_content)

            refined_text = result.get("refined_text", "")
            vocabulary_list = result.get("vocabulary", [])

            # Format vocabulary
            vocab_text = ""
            if vocabulary_list:
                vocab_text = "📝 <b>Vocabulary List</b>\n"
                for item in vocabulary_list:
                    word = item.get("word", "")
                    translation = item.get("translation", "")
                    if word and translation:
                        vocab_text += f"<b>{word}</b> – {translation}\n"

            logger.info(f"Groq API muvaffaqiyatli javob berdi (API key #{api_key_index + 1})")
            return refined_text, vocab_text

        except httpx.HTTPStatusError as e:
            logger.warning(f"API key #{api_key_index + 1} HTTP xatosi: {e.response.status_code}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None, None
        except json.JSONDecodeError as e:
            logger.warning(f"API key #{api_key_index + 1} JSON xatosi: {e}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None, None
        except Exception as e:
            logger.warning(f"API key #{api_key_index + 1} da xato: {e}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None, None

    return None, None
