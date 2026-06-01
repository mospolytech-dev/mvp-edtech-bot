from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import ApplicationCallback, applications_list_keyboard, back_keyboard
from database.crud.users import get_pending_users, update_user_status
from database.models.user import UserStatus

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
    else:
        decision = f"❌ Отклонено: <b>{user.full_name}</b>"
        user_text = (
            "❌ <b>Ваша заявка отклонена.</b>\n\n"
            "Обратитесь к администратору за подробностями."
        )

    await callback.message.edit_text(
        f"{decision}\nРешение принял: {callback.from_user.full_name}"
    )
    await callback.answer()

    try:
        await bot.send_message(user.telegram_id, user_text)
    except Exception:
        pass
