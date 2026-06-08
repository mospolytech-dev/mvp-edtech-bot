from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.filters.teacher import IsTeacher
from bot.keyboards.inline import teacher_menu_keyboard
from database.models.user import User

teacher_router = Router()
teacher_router.message.filter(IsTeacher())
teacher_router.callback_query.filter(IsTeacher())


@teacher_router.callback_query(F.data == "teacher:menu")
async def teacher_menu_handler(callback: CallbackQuery, teacher: User) -> None:
    await callback.message.edit_text(
        f"👋 Привет, <b>{teacher.full_name}</b>!",
        reply_markup=teacher_menu_keyboard(),
    )
    await callback.answer()


@teacher_router.callback_query(F.data == "teacher:noop")
async def teacher_noop(callback: CallbackQuery) -> None:
    await callback.answer()
