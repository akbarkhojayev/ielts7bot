import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from services.json_service import ensure_data_dir
from services.groq_service import generate_quiz_questions
from services.json_service import get_quiz_count, add_quizzes

from handlers import start_handler, quiz_handler, vocabulary_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Bot ishga tushmoqda...")

    ensure_data_dir()
    logger.info("Data papkasi tayyor")

    quiz_count = get_quiz_count()
    if quiz_count == 0:
        logger.info("Quiz savollari yo'q, Groq AI dan olinmoqda...")
        quizzes = await generate_quiz_questions()
        if quizzes:
            add_quizzes(quizzes)
            logger.info(f"{len(quizzes)} ta savol muvaffaqiyatli yuklandi")
        else:
            logger.warning("Groq API dan savol olishda xato! API key ni tekshiring.")
    else:
        logger.info(f"Mavjud quiz savollar soni: {quiz_count}")

    me = await bot.get_me()
    logger.info(f"Bot tayyor: @{me.username}")


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start_handler.router)
    dp.include_router(quiz_handler.router)
    dp.include_router(vocabulary_handler.router)

    dp.startup.register(on_startup)

    logger.info("Polling boshlandi...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Polling da xato: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot to'xtatildi")


if __name__ == "__main__":
    asyncio.run(main())
