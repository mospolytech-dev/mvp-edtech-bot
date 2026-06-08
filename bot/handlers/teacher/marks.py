from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.teacher import IsTeacher
from bot.keyboards.teacher import (
    TeacherActionCallback,
    TeacherMarkCallback,
    TeacherStudentCallback,
    teacher_mark_value_keyboard,
    teacher_student_list_keyboard,
)
from database.crud.lessons import get_lesson_by_id
from database.crud.marks import create_mark
from database.crud.users import get_students_by_group, get_user_by_id
from database.models.user import User

teacher_router = Router()
teacher_router.callback_query.filter(IsTeacher())


@teacher_router.callback_query(TeacherActionCallback.filter(F.action == "marks"))
async def show_student_list(
    callback: CallbackQuery,
    callback_data: TeacherActionCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    lesson = await get_lesson_by_id(session, callback_data.lesson_id)
    if lesson is None:
        await callback.answer("Занятие не найдено.", show_alert=True)
        return

    students = await get_students_by_group(session, lesson.group_id)
    if not students:
        await callback.answer("В группе нет студентов.", show_alert=True)
        return

    subject = lesson.subject.name if lesson.subject else "—"
    group = lesson.group.name if lesson.group else "—"
    await callback.message.edit_text(
        f"📊 <b>Оценки</b>\n{subject} | {group}\n\nВыберите студента:",
        reply_markup=teacher_student_list_keyboard(lesson.id, students),
    )
    await callback.answer()


@teacher_router.callback_query(TeacherStudentCallback.filter())
async def show_mark_keyboard(
    callback: CallbackQuery,
    callback_data: TeacherStudentCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    lesson = await get_lesson_by_id(session, callback_data.lesson_id)
    student = await get_user_by_id(session, callback_data.student_id)
    if lesson is None or student is None:
        await callback.answer("Данные не найдены.", show_alert=True)
        return

    subject = lesson.subject.name if lesson.subject else "—"
    await callback.message.edit_text(
        f"👤 <b>{student.full_name}</b>\n{subject}\n\nПоставьте оценку:",
        reply_markup=teacher_mark_value_keyboard(lesson.id, student.id),
    )
    await callback.answer()


@teacher_router.callback_query(TeacherMarkCallback.filter())
async def save_mark(
    callback: CallbackQuery,
    callback_data: TeacherMarkCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    await create_mark(
        session,
        student_id=callback_data.student_id,
        lesson_id=callback_data.lesson_id,
        teacher_id=teacher.id,
        value=callback_data.value,
    )

    student = await get_user_by_id(session, callback_data.student_id)
    lesson = await get_lesson_by_id(session, callback_data.lesson_id)
    student_name = student.full_name if student else "Студент"
    subject = lesson.subject.name if lesson else "—"

    from bot.keyboards.teacher import TeacherLessonCallback, lesson_detail_keyboard
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ К занятию",
        callback_data=TeacherLessonCallback(lesson_id=callback_data.lesson_id).pack(),
    ))
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="teacher:schedule"))

    await callback.message.edit_text(
        f"✅ Оценка <b>{callback_data.value}</b> выставлена\n"
        f"👤 {student_name}\n"
        f"📖 {subject}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
