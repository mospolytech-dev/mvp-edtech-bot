from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import config
from bot.keyboards.admin import ApplicationCallback, application_review_keyboard
from bot.keyboards.inline import RegGroupCallback, RegRoleCallback, group_selection_keyboard
from bot.states.user import RegistrationStates
from database.crud.groups import get_all_groups, get_group_by_id
from database.crud.users import create_user
from database.models.user import UserRole

registration_router = Router(name=__name__)

_ROLE_MAP: dict[str, UserRole] = {
    "student": UserRole.student,
    "teacher": UserRole.teacher,
    "admin": UserRole.admin,
}

_ROLE_LABELS: dict[str, str] = {
    "student": "Студент",
    "teacher": "Преподаватель",
    "admin": "Администратор",
}


@registration_router.callback_query(RegistrationStates.waiting_role, RegRoleCallback.filter())
async def pick_role(
    callback: CallbackQuery,
    callback_data: RegRoleCallback,
    state: FSMContext,
) -> None:
    await state.update_data(role=callback_data.role)
    await state.set_state(RegistrationStates.waiting_full_name)
    await callback.message.edit_text(
        f"Вы выбрали: <b>{_ROLE_LABELS[callback_data.role]}</b>\n\n"
        "Введите ваше <b>полное имя</b> (Фамилия Имя Отчество):"
    )
    await callback.answer()


@registration_router.message(RegistrationStates.waiting_full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Имя слишком короткое. Введите полное имя:")
        return

    data = await state.get_data()

    if data["role"] == "student":
        groups = await get_all_groups(session)
        if groups:
            await state.update_data(full_name=full_name)
            await state.set_state(RegistrationStates.waiting_group)
            await message.answer(
                "Выберите вашу <b>группу</b>:",
                reply_markup=group_selection_keyboard(groups),
            )
            return

    await _finish_registration(
        bot=message.bot,
        session=session,
        state=state,
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=full_name,
        role=_ROLE_MAP[data["role"]],
        group_id=None,
        answer_to=message,
    )


@registration_router.callback_query(RegistrationStates.waiting_group, RegGroupCallback.filter())
async def pick_group(
    callback: CallbackQuery,
    callback_data: RegGroupCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    group_id = callback_data.group_id if callback_data.group_id != 0 else None
    await callback.answer()
    await _finish_registration(
        bot=callback.bot,
        session=session,
        state=state,
        tg_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        role=_ROLE_MAP[data["role"]],
        group_id=group_id,
        answer_to=callback.message,
    )


async def _finish_registration(
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
    tg_id: int,
    username: str | None,
    full_name: str,
    role: UserRole,
    group_id: int | None,
    answer_to: Message,
) -> None:
    user = await create_user(session, tg_id, username, full_name, role, group_id)
    await state.clear()

    await answer_to.answer(
        "✅ <b>Заявка отправлена!</b>\n\n"
        "Администратор рассмотрит её и вы получите уведомление."
    )

    role_label = _ROLE_LABELS.get(role.value, role.value)
    username_str = f"@{username}" if username else "—"

    text = (
        "📋 <b>Новая заявка на регистрацию</b>\n\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"🎭 <b>Роль:</b> {role_label}\n"
        f"🔗 <b>Telegram:</b> {username_str}\n"
        f"🆔 <b>ID:</b> <code>{tg_id}</code>"
    )

    if group_id:
        group = await get_group_by_id(session, group_id)
        if group:
            text += f"\n👥 <b>Группа:</b> {group.name} ({group.year})"

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=application_review_keyboard(user.id),
            )
        except Exception:
            pass
