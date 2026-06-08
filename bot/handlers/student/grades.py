from collections import defaultdict

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.student import IsStudent
from bot.keyboards.student import back_to_student_menu
from database.crud.marks import get_marks_for_student
from database.models.user import User

student_router = Router()
student_router.callback_query.filter(IsStudent())


@student_router.callback_query(F.data == "menu:grades")
async def show_grades(callback: CallbackQuery, session: AsyncSession, student: User) -> None:
    marks = await get_marks_for_student(session, student.id)

    if not marks:
        await callback.message.edit_text(
            "Оценок пока нет.",
            reply_markup=back_to_student_menu(),
        )
        await callback.answer()
        return

    by_subject: dict[str, list[int]] = defaultdict(list)
    for mark in marks:
        subject_name = mark.lesson.subject.name if mark.lesson and mark.lesson.subject else "—"
        by_subject[subject_name].append(mark.value)

    lines = ["📊 <b>Мои оценки</b>\n"]
    for subject_name, values in by_subject.items():
        avg = round(sum(values) / len(values), 1)
        marks_str = ", ".join(str(v) for v in values)
        lines.append(f"<b>{subject_name}</b>")
        lines.append(f"  {marks_str} → среднее: {avg}")
        lines.append("")

    text = "\n".join(lines).rstrip()
    await callback.message.edit_text(text, reply_markup=back_to_student_menu())
    await callback.answer()
