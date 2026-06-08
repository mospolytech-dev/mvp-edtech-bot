from collections import defaultdict

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.student import IsStudent
from bot.keyboards.student import ATT_STATUS_LABEL, back_to_student_menu
from database.crud.attendance import get_attendance_for_student
from database.models.user import User

student_router = Router()
student_router.callback_query.filter(IsStudent())


@student_router.callback_query(F.data == "menu:attendance")
async def show_attendance(callback: CallbackQuery, session: AsyncSession, student: User) -> None:
    records = await get_attendance_for_student(session, student.id)

    if not records:
        await callback.message.edit_text(
            "Посещаемость не отмечена.",
            reply_markup=back_to_student_menu(),
        )
        await callback.answer()
        return

    total = len(records)
    counts: dict[str, int] = defaultdict(int)
    for rec in records:
        counts[rec.status.value] += 1

    present = counts.get("present", 0)
    absent = counts.get("absent", 0)
    late = counts.get("late", 0)
    excused = counts.get("excused", 0)
    present_pct = round(present / total * 100) if total > 0 else 0

    lines = [
        "✅ <b>Моя посещаемость</b>\n",
        f"Всего отмечено: {total}",
        f"✅ Присутствовал: {present} ({present_pct}%)",
        f"❌ Отсутствовал: {absent}",
        f"⏰ Опоздал: {late}",
        f"📋 Уважительная: {excused}",
        "",
    ]

    by_subject: dict[str, list] = defaultdict(list)
    for rec in records[:10]:
        subject_name = rec.lesson.subject.name if rec.lesson and rec.lesson.subject else "—"
        by_subject[subject_name].append(rec)

    for subject_name, recs in by_subject.items():
        lines.append(f"<b>{subject_name}</b>")
        for rec in recs:
            date_str = rec.date.strftime("%d.%m")
            status_label = ATT_STATUS_LABEL.get(rec.status.value, rec.status.value)
            lines.append(f"  {date_str} — {status_label}")
        lines.append("")

    text = "\n".join(lines).rstrip()
    await callback.message.edit_text(text, reply_markup=back_to_student_menu())
    await callback.answer()
