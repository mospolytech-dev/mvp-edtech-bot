from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import (
    GroupCallback,
    PageCallback,
    back_keyboard,
    confirm_delete_group_keyboard,
    groups_keyboard,
)
from bot.states.admin import AdminGroupStates
from database.crud.groups import create_group, delete_group, get_all_groups, get_group_by_id

admin_router = Router(name=__name__)
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


async def _show_groups(callback: CallbackQuery, session: AsyncSession, page: int = 0) -> None:
    groups = await get_all_groups(session)
    count = len(groups)
    header = f"🏫 <b>Группы</b> ({count})\n\n" if count else "🏫 <b>Группы</b>\n\nГрупп ещё нет.\n\n"
    await callback.message.edit_text(header, reply_markup=groups_keyboard(groups, page))


@admin_router.callback_query(F.data == "adm:groups")
async def show_groups(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_groups(callback, session, page=0)
    await callback.answer()


@admin_router.callback_query(PageCallback.filter(F.section == "groups"))
async def paginate_groups(
    callback: CallbackQuery, callback_data: PageCallback, session: AsyncSession
) -> None:
    await _show_groups(callback, session, page=callback_data.page)
    await callback.answer()


@admin_router.callback_query(F.data == "adm:groups:add")
async def start_add_group(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Введите название группы (например: <code>253-324</code>):")
    await state.update_data(msg_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await state.set_state(AdminGroupStates.waiting_name)
    await callback.answer()


@admin_router.message(AdminGroupStates.waiting_name)
async def process_group_name(message: Message, state: FSMContext, bot: Bot) -> None:
    name = message.text.strip()
    await message.delete()
    data = await state.get_data()

    if not name:
        await bot.edit_message_text(
            "Название не может быть пустым. Введите название группы:",
            chat_id=data["chat_id"], message_id=data["msg_id"],
        )
        return

    await state.update_data(name=name)
    await bot.edit_message_text(
        "Введите год набора (например: <code>2025</code>):",
        chat_id=data["chat_id"], message_id=data["msg_id"],
        parse_mode="HTML",
    )
    await state.set_state(AdminGroupStates.waiting_year)


@admin_router.message(AdminGroupStates.waiting_year)
async def process_group_year(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    text = message.text.strip()
    await message.delete()
    data = await state.get_data()

    if not text.isdigit() or not (2000 <= int(text) <= 2100):
        await bot.edit_message_text(
            "Введите корректный год (например: <code>2025</code>):",
            chat_id=data["chat_id"], message_id=data["msg_id"],
            parse_mode="HTML",
        )
        return

    group = await create_group(session, name=data["name"], year=int(text))
    await state.clear()

    await bot.edit_message_text(
        f"✅ Группа <b>{group.name}</b> ({group.year}) создана.",
        chat_id=data["chat_id"], message_id=data["msg_id"],
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )


@admin_router.callback_query(GroupCallback.filter(F.action == "delete"))
async def ask_delete_group(
    callback: CallbackQuery, callback_data: GroupCallback, session: AsyncSession
) -> None:
    group = await get_group_by_id(session, callback_data.group_id)
    if not group:
        await callback.answer("Группа не найдена.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Удалить группу <b>{group.name} ({group.year})</b>?\n\n"
        "⚠️ Все связанные занятия также будут удалены.",
        reply_markup=confirm_delete_group_keyboard(group.id),
        parse_mode="HTML",
    )
    await callback.answer()


@admin_router.callback_query(GroupCallback.filter(F.action == "confirm"))
async def confirm_delete_group(
    callback: CallbackQuery, callback_data: GroupCallback, session: AsyncSession
) -> None:
    deleted = await delete_group(session, callback_data.group_id)
    if not deleted:
        await callback.answer("Группа не найдена.", show_alert=True)
        return
    await _show_groups(callback, session, page=0)
    await callback.answer("Группа удалена.")
