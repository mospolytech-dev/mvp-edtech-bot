from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import config
from bot.keyboards.admin import admin_menu_keyboard
from bot.keyboards.inline import reapply_keyboard, role_selection_keyboard, student_menu_keyboard, teacher_menu_keyboard
from bot.states.user import RegistrationStates
from database.crud.users import get_user_by_telegram_id
from database.models.user import UserRole, UserStatus

start_router = Router(name=__name__)


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    tg_id = message.from_user.id

    if tg_id in config.admin_ids:
        await state.clear()
        await message.answer("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
        return

    user = await get_user_by_telegram_id(session, tg_id)

    if user is None:
        await state.set_state(RegistrationStates.waiting_role)
        await message.answer(
            "👋 Добро пожаловать!\n\nВыберите вашу роль для регистрации:",
            reply_markup=role_selection_keyboard(),
        )
        return

    if user.status == UserStatus.pending:
        await message.answer("⏳ Ваша заявка ещё на рассмотрении. Ожидайте уведомления.")
        return

    if user.status == UserStatus.rejected:
        await message.answer(
            "❌ <b>Ваша заявка была отклонена.</b>\n\n"
            "Вы можете исправить данные и подать повторно.",
            reply_markup=reapply_keyboard(),
        )
        return

    # active
    if user.role == UserRole.admin:
        await message.answer("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
    elif user.role == UserRole.teacher:
        await message.answer(
            f"👋 Привет, <b>{user.full_name}</b>!",
            reply_markup=teacher_menu_keyboard(),
        )
    else:
        await message.answer(
            f"👋 Привет, <b>{user.full_name}</b>!",
            reply_markup=student_menu_keyboard(),
        )
