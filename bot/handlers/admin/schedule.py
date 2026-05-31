from datetime import datetime, time

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import (
    LessonPickCallback,
    WEEKDAYS,
    admin_menu_keyboard,
    back_keyboard,
    pick_group_keyboard,
    pick_subject_keyboard,
    pick_teacher_keyboard,
    schedule_keyboard,
)
from bot.states.admin import AdminLessonStates
from database.crud.groups import get_all_groups
from database.crud.lessons import create_lesson, get_all_lessons
from database.crud.subjects import get_all_subjects
from database.crud.users import get_teachers

admin_router = Router(name=__name__)
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.callback_query(F.data == "adm:schedule")
async def show_schedule(callback: CallbackQuery, session: AsyncSession) -> None:
    lessons = await get_all_lessons(session)

    if not lessons:
        text = "📅 <b>Расписание</b>\n\nЗанятий ещё нет."
    else:
        lines = []
        for les in lessons:
            day = WEEKDAYS.get(les.weekday, str(les.weekday))
            start = les.start_time.strftime("%H:%M")
            end = les.end_time.strftime("%H:%M")
            room = f" · {les.room}" if les.room else ""
            lines.append(
                f"• {les.subject.name} | {les.group.name} | {day} {start}–{end}{room}\n"
                f"  👨‍🏫 {les.teacher.full_name}"
            )
        text = "📅 <b>Расписание</b>\n\n" + "\n\n".join(lines)

    await callback.message.edit_text(text, reply_markup=schedule_keyboard(lessons))
    await callback.answer()


@admin_router.callback_query(F.data == "adm:schedule:add")
async def start_add_lesson(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    subjects = await get_all_subjects(session)
    if not subjects:
        await callback.answer("Сначала создайте хотя бы одну дисциплину.", show_alert=True)
        return
    await callback.message.edit_text("Выберите дисциплину:", reply_markup=pick_subject_keyboard(subjects))
    await state.update_data(msg_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await state.set_state(AdminLessonStates.waiting_subject)
    await callback.answer()


@admin_router.callback_query(AdminLessonStates.waiting_subject, LessonPickCallback.filter(F.kind == "subject"))
async def pick_subject(
    callback: CallbackQuery, callback_data: LessonPickCallback, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(subject_id=callback_data.value)
    teachers = await get_teachers(session)
    if not teachers:
        await callback.answer("Нет ни одного преподавателя с активным аккаунтом.", show_alert=True)
        return
    await callback.message.edit_text("Выберите преподавателя:", reply_markup=pick_teacher_keyboard(teachers))
    await state.set_state(AdminLessonStates.waiting_teacher)
    await callback.answer()


@admin_router.callback_query(AdminLessonStates.waiting_teacher, LessonPickCallback.filter(F.kind == "teacher"))
async def pick_teacher(
    callback: CallbackQuery, callback_data: LessonPickCallback, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(teacher_id=callback_data.value)
    groups = await get_all_groups(session)
    if not groups:
        await callback.answer("Сначала создайте хотя бы одну группу.", show_alert=True)
        return
    await callback.message.edit_text("Выберите группу:", reply_markup=pick_group_keyboard(groups))
    await state.set_state(AdminLessonStates.waiting_group)
    await callback.answer()


@admin_router.callback_query(AdminLessonStates.waiting_group, LessonPickCallback.filter(F.kind == "group"))
async def pick_group(
    callback: CallbackQuery, callback_data: LessonPickCallback, state: FSMContext
) -> None:
    await state.update_data(group_id=callback_data.value)
    await callback.message.edit_text(
        "Выберите дату занятия:",
        reply_markup=await SimpleCalendar().start_calendar(),
    )
    await state.set_state(AdminLessonStates.waiting_weekday)
    await callback.answer()


@admin_router.callback_query(AdminLessonStates.waiting_weekday, SimpleCalendarCallback.filter())
async def pick_date(
    callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext, bot: Bot
) -> None:
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if not selected:
        return

    # isoweekday(): 1=Пн … 7=Вс — совпадает с нашей схемой
    weekday = date.isoweekday()
    await state.update_data(weekday=weekday)

    data = await state.get_data()
    day_name = WEEKDAYS[weekday]
    await bot.edit_message_text(
        f"Дата: {date.strftime('%d.%m.%Y')} ({day_name})\n\n"
        "Введите время начала занятия (формат: <code>09:00</code>):",
        chat_id=data["chat_id"], message_id=data["msg_id"],
        parse_mode="HTML",
    )
    await state.set_state(AdminLessonStates.waiting_start_time)


@admin_router.message(AdminLessonStates.waiting_start_time)
async def process_start_time(message: Message, state: FSMContext, bot: Bot) -> None:
    t = _parse_time(message.text.strip())
    await message.delete()
    data = await state.get_data()

    if t is None:
        await bot.edit_message_text(
            "Неверный формат. Введите время в виде <code>09:00</code>:",
            chat_id=data["chat_id"], message_id=data["msg_id"], parse_mode="HTML",
        )
        return

    await state.update_data(start_time=t)
    await bot.edit_message_text(
        "Введите время окончания занятия (формат: <code>10:30</code>):",
        chat_id=data["chat_id"], message_id=data["msg_id"], parse_mode="HTML",
    )
    await state.set_state(AdminLessonStates.waiting_end_time)


@admin_router.message(AdminLessonStates.waiting_end_time)
async def process_end_time(message: Message, state: FSMContext, bot: Bot) -> None:
    t = _parse_time(message.text.strip())
    await message.delete()
    data = await state.get_data()

    if t is None:
        await bot.edit_message_text(
            "Неверный формат. Введите время в виде <code>10:30</code>:",
            chat_id=data["chat_id"], message_id=data["msg_id"], parse_mode="HTML",
        )
        return
    if t <= data["start_time"]:
        await bot.edit_message_text(
            "Время окончания должно быть позже времени начала. Введите снова:",
            chat_id=data["chat_id"], message_id=data["msg_id"],
        )
        return

    await state.update_data(end_time=t)
    await bot.edit_message_text(
        "Введите аудиторию (или <code>-</code> чтобы пропустить):",
        chat_id=data["chat_id"], message_id=data["msg_id"], parse_mode="HTML",
    )
    await state.set_state(AdminLessonStates.waiting_room)


@admin_router.message(AdminLessonStates.waiting_room)
async def process_room(message: Message, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    room = None if message.text.strip() == "-" else message.text.strip()
    await message.delete()
    data = await state.get_data()

    lesson = await create_lesson(
        session=session,
        subject_id=data["subject_id"],
        teacher_id=data["teacher_id"],
        group_id=data["group_id"],
        weekday=data["weekday"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        room=room,
    )
    await state.clear()

    day = WEEKDAYS[lesson.weekday]
    start = lesson.start_time.strftime("%H:%M")
    end = lesson.end_time.strftime("%H:%M")
    room_text = f" · ауд. {lesson.room}" if lesson.room else ""

    await bot.edit_message_text(
        f"✅ Занятие добавлено:\n{day} {start}–{end}{room_text}",
        chat_id=data["chat_id"], message_id=data["msg_id"],
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )


@admin_router.callback_query(F.data == "adm:cancel")
async def cancel_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
    await callback.answer("Отменено")


def _parse_time(text: str) -> time | None:
    for fmt in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None
