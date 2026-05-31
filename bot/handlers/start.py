from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import config
from bot.keyboards.admin import admin_menu_keyboard
from bot.keyboards.inline import main_menu_keyboard

start_router = Router(name=__name__)


@start_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user.id in config.admin_ids:
        await message.answer("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("Привет! Это MVP EdTech Bot.", reply_markup=main_menu_keyboard())
