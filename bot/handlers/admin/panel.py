from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import admin_menu_keyboard

admin_router = Router(name=__name__)
admin_router.callback_query.filter(IsAdmin())


@admin_router.callback_query(F.data == "adm:menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
    await callback.answer()


@admin_router.callback_query(F.data == "adm:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()
