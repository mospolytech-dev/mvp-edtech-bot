from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import back_keyboard
from database.crud.users import get_all_active_users
from database.models.user import UserRole

admin_router = Router(name=__name__)
admin_router.callback_query.filter(IsAdmin())

ROLE_LABELS = {
    UserRole.student: "Студент",
    UserRole.teacher: "Преподаватель",
    UserRole.admin: "Админ",
}


@admin_router.callback_query(F.data == "adm:users")
async def show_users(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await get_all_active_users(session)

    if not users:
        text = "👥 <b>Пользователи</b>\n\nСписок пуст."
    else:
        lines = []
        for u in users:
            role = ROLE_LABELS.get(u.role, u.role)
            group = f" · {u.group.name}" if u.group else ""
            lines.append(f"• {u.full_name} — {role}{group}")
        text = "👥 <b>Пользователи</b>\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=back_keyboard())
    await callback.answer()
