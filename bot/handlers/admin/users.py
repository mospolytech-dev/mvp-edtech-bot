from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import back_keyboard
from database.crud.users import get_all_active_users
from database.models.user import UserRole

admin_router = Router(name=__name__)
admin_router.callback_query.filter(IsAdmin())


@admin_router.callback_query(F.data == "adm:users")
async def show_users(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await get_all_active_users(session)

    teachers = [u for u in users if u.role == UserRole.teacher]
    students = [u for u in users if u.role == UserRole.student]

    lines = ["👥 <b>Пользователи</b>"]

    lines.append(f"\n👨‍🏫 <b>Преподаватели</b> ({len(teachers)})")
    if teachers:
        for i, u in enumerate(teachers, 1):
            lines.append(f"  {i}. {u.full_name}")
    else:
        lines.append("  — нет")

    lines.append(f"\n👨‍🎓 <b>Студенты</b> ({len(students)})")
    if students:
        for i, u in enumerate(students, 1):
            group = f" · <i>{u.group.name}</i>" if u.group else ""
            lines.append(f"  {i}. {u.full_name}{group}")
    else:
        lines.append("  — нет")

    await callback.message.edit_text("\n".join(lines), reply_markup=back_keyboard())
    await callback.answer()
