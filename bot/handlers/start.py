from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.inline import main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        text="Привет! Это MVP EdTech Bot 🚀",
        reply_markup=main_menu_keyboard(),
    )
