from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.teacher import IsTeacher
from bot.keyboards.teacher import (
    TeacherLessonCallback,
    TeacherLessonPageCallback,
    WEEKDAYS,
    lesson_detail_keyboard,
    teacher_schedule_keyboard,
)
from database.crud.lessons import get_lesson_by_id, get_lessons_for_teacher
from database.models.user import User

teacher_router = Router()
teacher_router.callback_query.filter(IsTeacher())


async def _show_schedule(callback: CallbackQuery, session: AsyncSession, teacher: User, page: int = 0) -> None:
    lessons = await get_lessons_for_teacher(session, teacher.id)
    if not lessons:
        from bot.keyboards.inline import teacher_menu_keyboard
        await callback.message.edit_text("Занятий нет.", reply_markup=teacher_menu_keyboard())
        await callback.answer()
        return
    await callback.message.edit_text(
        "📅 <b>Расписание</b>\n\nВыберите занятие:",
        reply_markup=teacher_schedule_keyboard(lessons, page),
    )
    await callback.answer()


@teacher_router.callback_query(F.data.in_({"teacher:schedule", "menu:schedule"}))
async def show_schedule(callback: CallbackQuery, session: AsyncSession, teacher: User) -> None:
    await _show_schedule(callback, session, teacher, page=0)


@teacher_router.callback_query(TeacherLessonPageCallback.filter())
async def paginate_schedule(
    callback: CallbackQuery,
    callback_data: TeacherLessonPageCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    await _show_schedule(callback, session, teacher, page=callback_data.page)


@teacher_router.callback_query(TeacherLessonCallback.filter())
async def show_lesson_detail(
    callback: CallbackQuery,
    callback_data: TeacherLessonCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    lesson = await get_lesson_by_id(session, callback_data.lesson_id)
    if lesson is None:
        await callback.answer("Занятие не найдено.", show_alert=True)
        return

    day = WEEKDAYS.get(lesson.weekday, str(lesson.weekday))
    start = lesson.start_time.strftime("%H:%M")
    end = lesson.end_time.strftime("%H:%M")
    subject = lesson.subject.name if lesson.subject else "—"
    group = lesson.group.name if lesson.group else "—"
    room = f"\nАудитория: {lesson.room}" if lesson.room else ""

    text = (
        f"📖 <b>{subject}</b>\n"
        f"Группа: {group}\n"
        f"{day}  {start}–{end}{room}"
    )
    await callback.message.edit_text(text, reply_markup=lesson_detail_keyboard(lesson.id))
    await callback.answer()
