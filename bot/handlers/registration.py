import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import config
from bot.keyboards.admin import ApplicationCallback, application_review_keyboard
from bot.keyboards.inline import (
    RegGroupCallback,
    RegGroupPageCallback,
    RegRoleCallback,
    RegSubjectCallback,
    RegSubjectPageCallback,
    group_selection_keyboard,
    role_selection_keyboard,
    subject_selection_keyboard,
)
from bot.states.user import RegistrationStates
from database.crud.groups import get_all_groups, get_group_by_id
from database.crud.subjects import get_all_subjects
from database.crud.users import create_user, delete_user_by_telegram_id
from database.models.user import UserRole

_CYRILLIC_WORD = re.compile(r'^[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?$')


def _validate_full_name(name: str) -> str | None:
    """Возвращает текст ошибки или None если имя корректно."""
    words = name.split()
    if len(words) < 2:
        return "Введите минимум 2 слова — фамилию и имя."
    if len(words) > 3:
        return "Слишком много слов. Формат: <b>Фамилия Имя Отчество</b>"
    for word in words:
        if not _CYRILLIC_WORD.match(word):
            return (
                "Используйте только русские буквы, каждое слово с заглавной.\n"
                "Пример: <b>Иванов Иван Иванович</b>"
            )
    return None

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


@registration_router.callback_query(F.data == "reg:reapply")
async def reapply(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await delete_user_by_telegram_id(session, callback.from_user.id)
    await state.set_state(RegistrationStates.waiting_role)
    await callback.message.edit_text(
        "Выберите вашу роль для регистрации:",
        reply_markup=role_selection_keyboard(),
    )
    await callback.answer()


@registration_router.message(RegistrationStates.waiting_full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    full_name = (message.text or "").strip()
    error = _validate_full_name(full_name)
    if error:
        await message.answer(error)
        return

    data = await state.get_data()
    await state.update_data(full_name=full_name)

    if data["role"] == "student":
        groups = await get_all_groups(session)
        if groups:
            await state.set_state(RegistrationStates.waiting_group)
            await message.answer(
                "Выберите вашу <b>группу</b>:",
                reply_markup=group_selection_keyboard(groups),
            )
            return

    if data["role"] == "teacher":
        subjects = await get_all_subjects(session)
        if subjects:
            await state.update_data(selected_subjects=[])
            await state.set_state(RegistrationStates.waiting_subjects)
            await message.answer(
                "Выберите <b>дисциплины</b>, которые вы преподаёте\n"
                "(можно выбрать несколько, затем нажмите «Готово»):",
                reply_markup=subject_selection_keyboard(subjects, set(), 0),
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
        subject_names=[],
        answer_to=message,
    )


# ── Студент: пагинация групп ──────────────────────────────────────────────────

@registration_router.callback_query(RegistrationStates.waiting_group, RegGroupPageCallback.filter())
async def paginate_reg_groups(
    callback: CallbackQuery,
    callback_data: RegGroupPageCallback,
    session: AsyncSession,
) -> None:
    groups = await get_all_groups(session)
    await callback.message.edit_reply_markup(
        reply_markup=group_selection_keyboard(groups, callback_data.page),
    )
    await callback.answer()


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
        subject_names=[],
        answer_to=callback.message,
    )


# ── Преподаватель: выбор дисциплин ────────────────────────────────────────────

@registration_router.callback_query(RegistrationStates.waiting_subjects, RegSubjectCallback.filter())
async def toggle_subject(
    callback: CallbackQuery,
    callback_data: RegSubjectCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    selected: set[int] = set(data.get("selected_subjects", []))
    if callback_data.subject_id in selected:
        selected.discard(callback_data.subject_id)
    else:
        selected.add(callback_data.subject_id)
    await state.update_data(selected_subjects=list(selected))

    subjects = await get_all_subjects(session)
    await callback.message.edit_reply_markup(
        reply_markup=subject_selection_keyboard(subjects, selected, callback_data.page),
    )
    await callback.answer()


@registration_router.callback_query(RegistrationStates.waiting_subjects, RegSubjectPageCallback.filter())
async def paginate_reg_subjects(
    callback: CallbackQuery,
    callback_data: RegSubjectPageCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    selected: set[int] = set(data.get("selected_subjects", []))
    subjects = await get_all_subjects(session)
    await callback.message.edit_reply_markup(
        reply_markup=subject_selection_keyboard(subjects, selected, callback_data.page),
    )
    await callback.answer()


@registration_router.callback_query(RegistrationStates.waiting_subjects, F.data == "reg:subjects_done")
async def finish_subject_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    selected_ids: list[int] = data.get("selected_subjects", [])

    subject_names: list[str] = []
    if selected_ids:
        all_subjects = await get_all_subjects(session)
        subject_names = [s.name for s in all_subjects if s.id in set(selected_ids)]

    await callback.answer()
    await _finish_registration(
        bot=callback.bot,
        session=session,
        state=state,
        tg_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        role=_ROLE_MAP[data["role"]],
        group_id=None,
        subject_names=subject_names,
        answer_to=callback.message,
    )


# ── Noop ──────────────────────────────────────────────────────────────────────

@registration_router.callback_query(F.data == "reg:noop")
async def reg_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ── Финализация ───────────────────────────────────────────────────────────────

async def _finish_registration(
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
    tg_id: int,
    username: str | None,
    full_name: str,
    role: UserRole,
    group_id: int | None,
    subject_names: list[str],
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
        from database.crud.groups import get_group_by_id
        group = await get_group_by_id(session, group_id)
        if group:
            text += f"\n👥 <b>Группа:</b> {group.name} ({group.year})"

    if subject_names:
        text += f"\n📚 <b>Дисциплины:</b> {', '.join(subject_names)}"

    if role == UserRole.admin:
        text += (
            f"\n\n⚙️ <b>Для активации прав администратора</b> добавьте ID "
            f"<code>{tg_id}</code> в переменную <code>ADMIN_IDS</code> в файле "
            f"<code>.env</code> и перезапустите бота.\n"
            f"<i>(В будущем это будет происходить автоматически без правки .env)</i>"
        )

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=application_review_keyboard(user.id),
            )
        except Exception:
            pass
