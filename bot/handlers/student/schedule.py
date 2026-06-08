from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.student import IsStudent
from bot.keyboards.student import WEEKDAYS, back_to_student_menu
from database.crud.lessons import get_lessons_for_group
from database.models.user import User

student_router = Router()
student_router.callback_query.filter(IsStudent())


def _shorten_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."
    return full_name


@student_router.callback_query(F.data == "menu:schedule")
async def show_schedule(callback: CallbackQuery, session: AsyncSession, student: User) -> None:
    if student.group_id is None:
        await callback.message.edit_text(
            "Вы не привязаны к группе.",
            reply_markup=back_to_student_menu(),
        )
        await callback.answer()
        return

    lessons = await get_lessons_for_group(session, student.group_id)
    if not lessons:
        await callback.message.edit_text(
            "Расписание не добавлено.",
            reply_markup=back_to_student_menu(),
        )
        await callback.answer()
        return

    by_weekday: dict[int, list] = {}
    for lesson in lessons:
        by_weekday.setdefault(lesson.weekday, []).append(lesson)

    lines = ["📅 <b>Расписание</b>\n"]
    for day_num in sorted(by_weekday.keys()):
        day_label = WEEKDAYS.get(day_num, str(day_num))
        lines.append(f"<b>{day_label}</b>")
        for lesson in by_weekday[day_num]:
            start = lesson.start_time.strftime("%H:%M")
            end = lesson.end_time.strftime("%H:%M")
            subject = lesson.subject.name if lesson.subject else "—"
            teacher_name = _shorten_name(lesson.teacher.full_name) if lesson.teacher else "—"
            room = f" · ауд. {lesson.room}" if lesson.room else ""
            lines.append(f"  • {start}–{end}  {subject}  👨‍🏫 {teacher_name}{room}")
        lines.append("")

    text = "\n".join(lines).rstrip()
    await callback.message.edit_text(text, reply_markup=back_to_student_menu())
    await callback.answer()
