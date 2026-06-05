from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import (
    ApplicationCallback,
    application_detail_keyboard,
    applications_list_keyboard,
    back_keyboard,
)
from bot.keyboards.inline import reapply_keyboard
from database.crud.users import get_pending_users, get_user_by_id, update_user_status
from database.models.user import UserRole, UserStatus

_ROLE_LABELS = {
    UserRole.student: "Студент",
    UserRole.teacher: "Преподаватель",
    UserRole.admin: "Администратор",
}

applications_router = Router(name=__name__)
applications_router.callback_query.filter(IsAdmin())


@applications_router.callback_query(F.data == "adm:applications")
async def show_applications(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await get_pending_users(session)
    if not users:
        await callback.message.edit_text(
            "📋 <b>Заявки</b>\n\nНет новых заявок.",
            reply_markup=back_keyboard(),
        )
    else:
        await callback.message.edit_text(
            f"📋 <b>Заявки на регистрацию</b> — {len(users)} шт.",
            reply_markup=applications_list_keyboard(users),
        )
    await callback.answer()


@applications_router.callback_query(ApplicationCallback.filter(F.action == "view"))
async def view_application(
    callback: CallbackQuery,
    callback_data: ApplicationCallback,
    session: AsyncSession,
) -> None:
    user = await get_user_by_id(session, callback_data.user_id)
    if user is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    role = _ROLE_LABELS.get(user.role, user.role.value)
    username_str = f"@{user.username}" if user.username else "—"

    text = (
        "📋 <b>Заявка на регистрацию</b>\n\n"
        f"👤 <b>Имя:</b> {user.full_name}\n"
        f"🎭 <b>Роль:</b> {role}\n"
        f"🔗 <b>Telegram:</b> {username_str}\n"
        f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>"
    )
    if user.group:
        text += f"\n👥 <b>Группа:</b> {user.group.name} ({user.group.year})"

    if user.role == UserRole.admin:
        text += (
            f"\n\n⚙️ <b>Для активации прав администратора</b> добавьте ID "
            f"<code>{user.telegram_id}</code> в <code>ADMIN_IDS</code> в файле "
            f"<code>.env</code> и перезапустите бота."
        )

    await callback.message.edit_text(text, reply_markup=application_detail_keyboard(user.id))
    await callback.answer()


@applications_router.callback_query(ApplicationCallback.filter(F.action.in_({"approve", "reject"})))
async def handle_application(
    callback: CallbackQuery,
    callback_data: ApplicationCallback,
    session: AsyncSession,
    bot: Bot,
) -> None:
    new_status = UserStatus.active if callback_data.action == "approve" else UserStatus.rejected
    user = await update_user_status(session, callback_data.user_id, new_status)

    if user is None:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    if callback_data.action == "approve":
        decision = f"✅ Одобрено: <b>{user.full_name}</b>"
        user_text = (
            "✅ <b>Ваша заявка одобрена!</b>\n\n"
            "Теперь вы можете пользоваться ботом. Напишите /start"
        )
        if user.role == UserRole.admin:
            decision += (
                f"\n\n⚙️ Не забудьте добавить ID <code>{user.telegram_id}</code> "
                f"в <code>ADMIN_IDS</code> в <code>.env</code> и перезапустить бота."
            )
    else:
        decision = f"❌ Отклонено: <b>{user.full_name}</b>"
        user_text = (
            "❌ <b>Ваша заявка отклонена.</b>\n\n"
            "Вы можете исправить данные и подать повторно."
        )

    await callback.message.edit_text(
        f"{decision}\nРешение принял: {callback.from_user.full_name}"
    )
    await callback.answer()

    try:
        markup = reapply_keyboard() if callback_data.action == "reject" else None
        await bot.send_message(user.telegram_id, user_text, reply_markup=markup)
    except Exception:
        pass
