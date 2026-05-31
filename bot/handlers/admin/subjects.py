from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import (
    PageCallback,
    SubjectCallback,
    back_keyboard,
    confirm_delete_subject_keyboard,
    subjects_keyboard,
)
from bot.states.admin import AdminSubjectStates
from database.crud.subjects import (
    create_subject,
    delete_subject,
    get_all_subjects,
    get_subject_by_id,
)

admin_router = Router(name=__name__)
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


async def _show_subjects(callback: CallbackQuery, session: AsyncSession, page: int = 0) -> None:
    subjects = await get_all_subjects(session)
    count = len(subjects)
    header = f"📚 <b>Дисциплины</b> ({count})\n\n" if count else "📚 <b>Дисциплины</b>\n\nДисциплин ещё нет.\n\n"
    await callback.message.edit_text(header, reply_markup=subjects_keyboard(subjects, page))


@admin_router.callback_query(F.data == "adm:subjects")
async def show_subjects(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_subjects(callback, session, page=0)
    await callback.answer()


@admin_router.callback_query(PageCallback.filter(F.section == "subjects"))
async def paginate_subjects(
    callback: CallbackQuery, callback_data: PageCallback, session: AsyncSession
) -> None:
    await _show_subjects(callback, session, page=callback_data.page)
    await callback.answer()


@admin_router.callback_query(F.data == "adm:subjects:add")
async def start_add_subject(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Введите название дисциплины (например: <code>Математика</code>):")
    await state.update_data(msg_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await state.set_state(AdminSubjectStates.waiting_name)
    await callback.answer()


@admin_router.message(AdminSubjectStates.waiting_name)
async def process_subject_name(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    name = message.text.strip()
    await message.delete()
    data = await state.get_data()

    if not name:
        await bot.edit_message_text(
            "Название не может быть пустым. Введите название дисциплины:",
            chat_id=data["chat_id"], message_id=data["msg_id"],
        )
        return

    subject = await create_subject(session, name=name)
    await state.clear()

    await bot.edit_message_text(
        f"✅ Дисциплина <b>{subject.name}</b> создана.",
        chat_id=data["chat_id"], message_id=data["msg_id"],
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )


@admin_router.callback_query(SubjectCallback.filter(F.action == "delete"))
async def ask_delete_subject(
    callback: CallbackQuery, callback_data: SubjectCallback, session: AsyncSession
) -> None:
    subject = await get_subject_by_id(session, callback_data.subject_id)
    if not subject:
        await callback.answer("Дисциплина не найдена.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Удалить дисциплину <b>{subject.name}</b>?\n\n"
        "⚠️ Все связанные занятия также будут удалены.",
        reply_markup=confirm_delete_subject_keyboard(subject.id),
        parse_mode="HTML",
    )
    await callback.answer()


@admin_router.callback_query(SubjectCallback.filter(F.action == "confirm"))
async def confirm_delete_subject(
    callback: CallbackQuery, callback_data: SubjectCallback, session: AsyncSession
) -> None:
    deleted = await delete_subject(session, callback_data.subject_id)
    if not deleted:
        await callback.answer("Дисциплина не найдена.", show_alert=True)
        return
    await _show_subjects(callback, session, page=0)
    await callback.answer("Дисциплина удалена.")
