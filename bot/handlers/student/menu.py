from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.filters.student import IsStudent
from bot.keyboards.inline import student_menu_keyboard
from database.models.user import User

student_router = Router()
student_router.message.filter(IsStudent())
student_router.callback_query.filter(IsStudent())


@student_router.callback_query(F.data == "student:menu")
async def student_menu_handler(callback: CallbackQuery, student: User) -> None:
    await callback.message.edit_text(
        f"👋 Привет, <b>{student.full_name}</b>!",
        reply_markup=student_menu_keyboard(),
    )
    await callback.answer()


@student_router.callback_query(F.data == "student:noop")
async def student_noop(callback: CallbackQuery) -> None:
    await callback.answer()
