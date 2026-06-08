from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.teacher import IsTeacher
from bot.keyboards.teacher import (
    TeacherActionCallback,
    TeacherAttCallback,
    teacher_attendance_keyboard,
)
from database.crud.attendance import get_attendance_for_lesson, upsert_attendance
from database.crud.lessons import get_lesson_by_id
from database.crud.users import get_students_by_group
from database.models.attendance import AttendanceStatus
from database.models.user import User

teacher_router = Router()
teacher_router.callback_query.filter(IsTeacher())


def _build_att_map(records: list, student_ids: list[int]) -> dict[int, str]:
    att_map = {sid: "none" for sid in student_ids}
    for rec in records:
        att_map[rec.student_id] = rec.status.value
    return att_map


@teacher_router.callback_query(TeacherActionCallback.filter(F.action == "att"))
async def show_attendance_board(
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
    today = date.today()
    records = await get_attendance_for_lesson(session, lesson.id, today)
    att_map = _build_att_map(records, [s.id for s in students])

    subject = lesson.subject.name if lesson.subject else "—"
    group = lesson.group.name if lesson.group else "—"
    start = lesson.start_time.strftime("%H:%M")

    if not students:
        await callback.answer("В группе нет студентов.", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ <b>Посещаемость</b>\n{subject} | {group} | {start}\n\nНажмите на студента чтобы изменить статус:",
        reply_markup=teacher_attendance_keyboard(
            lesson_id=lesson.id,
            students=students,
            att_map=att_map,
            date_iso=today.isoformat(),
        ),
    )
    await callback.answer()


@teacher_router.callback_query(TeacherAttCallback.filter())
async def toggle_attendance(
    callback: CallbackQuery,
    callback_data: TeacherAttCallback,
    session: AsyncSession,
    teacher: User,
) -> None:
    att_date = date.fromisoformat(callback_data.date_iso)
    await upsert_attendance(
        session,
        lesson_id=callback_data.lesson_id,
        student_id=callback_data.student_id,
        date_=att_date,
        status=AttendanceStatus(callback_data.next_status),
    )

    lesson = await get_lesson_by_id(session, callback_data.lesson_id)
    students = await get_students_by_group(session, lesson.group_id)
    records = await get_attendance_for_lesson(session, callback_data.lesson_id, att_date)
    att_map = _build_att_map(records, [s.id for s in students])

    await callback.message.edit_reply_markup(
        reply_markup=teacher_attendance_keyboard(
            lesson_id=callback_data.lesson_id,
            students=students,
            att_map=att_map,
            date_iso=callback_data.date_iso,
        )
    )
    await callback.answer()
