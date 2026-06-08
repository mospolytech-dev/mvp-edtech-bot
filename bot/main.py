import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.handlers.registration import registration_router
from bot.handlers.start import start_router
from bot.handlers.teacher import (
    menu_router as teacher_menu_router,
    schedule_router as teacher_schedule_router,
    attendance_router as teacher_attendance_router,
    marks_router as teacher_marks_router,
)
from bot.handlers.admin import (
    applications_router,
    groups_router,
    panel_router,
    schedule_router,
    subjects_router,
    users_router,
)
from bot.middlewares.db import DbSessionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware())

    dp.include_routers(
        panel_router,
        applications_router,
        groups_router,
        subjects_router,
        schedule_router,
        users_router,
        teacher_menu_router,
        teacher_schedule_router,
        teacher_attendance_router,
        teacher_marks_router,
        registration_router,
        start_router,
    )

    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
