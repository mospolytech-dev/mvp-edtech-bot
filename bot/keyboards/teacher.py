from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.lesson import Lesson
from database.models.user import User

WEEKDAYS = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}
PER_PAGE = 8

ATT_STATUS_EMOJI = {
    "none": "⬜",
    "present": "✅",
    "absent": "❌",
    "late": "⏰",
}

ATT_NEXT = {
    "none": "present",
    "present": "absent",
    "absent": "late",
    "late": "present",
}


class TeacherLessonCallback(CallbackData, prefix="tl"):
    lesson_id: int


class TeacherLessonPageCallback(CallbackData, prefix="tlpg"):
    page: int


class TeacherActionCallback(CallbackData, prefix="tact"):
    lesson_id: int
    action: str  # "att" or "marks"


class TeacherAttCallback(CallbackData, prefix="ta"):
    lesson_id: int
    student_id: int
    next_status: str
    date_iso: str


class TeacherStudentCallback(CallbackData, prefix="ts_"):
    lesson_id: int
    student_id: int


class TeacherMarkCallback(CallbackData, prefix="tmk"):
    lesson_id: int
    student_id: int
    value: int


def _shorten_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."
    return full_name


def teacher_schedule_keyboard(lessons: list[Lesson], page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_items = lessons[page * PER_PAGE: (page + 1) * PER_PAGE]
    for lesson in page_items:
        day = WEEKDAYS.get(lesson.weekday, str(lesson.weekday))
        start = lesson.start_time.strftime("%H:%M")
        subject = lesson.subject.name if lesson.subject else "—"
        group = lesson.group.name if lesson.group else "—"
        builder.row(InlineKeyboardButton(
            text=f"{day} {start}  {subject}  ({group})",
            callback_data=TeacherLessonCallback(lesson_id=lesson.id).pack(),
        ))

    total = len(lessons)
    if total > PER_PAGE:
        total_pages = (total - 1) // PER_PAGE + 1
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(
                text="◀️", callback_data=TeacherLessonPageCallback(page=page - 1).pack()
            ))
        nav.append(InlineKeyboardButton(text=f"{page + 1} / {total_pages}", callback_data="teacher:noop"))
        if (page + 1) * PER_PAGE < total:
            nav.append(InlineKeyboardButton(
                text="▶️", callback_data=TeacherLessonPageCallback(page=page + 1).pack()
            ))
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text="⬅️ В меню", callback_data="teacher:menu"))
    return builder.as_markup()


def lesson_detail_keyboard(lesson_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Отметить посещаемость",
            callback_data=TeacherActionCallback(lesson_id=lesson_id, action="att").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Выставить оценки",
            callback_data=TeacherActionCallback(lesson_id=lesson_id, action="marks").pack(),
        )
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="teacher:schedule"))
    return builder.as_markup()


def teacher_attendance_keyboard(
    lesson_id: int,
    students: list[User],
    att_map: dict[int, str],
    date_iso: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for student in students:
        current = att_map.get(student.id, "none")
        emoji = ATT_STATUS_EMOJI.get(current, "⬜")
        next_s = ATT_NEXT.get(current, "present")
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {_shorten_name(student.full_name)}",
            callback_data=TeacherAttCallback(
                lesson_id=lesson_id,
                student_id=student.id,
                next_status=next_s,
                date_iso=date_iso,
            ).pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=TeacherLessonCallback(lesson_id=lesson_id).pack(),
    ))
    return builder.as_markup()


def teacher_student_list_keyboard(lesson_id: int, students: list[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for student in students:
        builder.row(InlineKeyboardButton(
            text=f"👤 {student.full_name}",
            callback_data=TeacherStudentCallback(lesson_id=lesson_id, student_id=student.id).pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=TeacherLessonCallback(lesson_id=lesson_id).pack(),
    ))
    return builder.as_markup()


def teacher_mark_value_keyboard(lesson_id: int, student_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(*[
        InlineKeyboardButton(
            text=str(v),
            callback_data=TeacherMarkCallback(lesson_id=lesson_id, student_id=student_id, value=v).pack(),
        )
        for v in range(1, 6)
    ])
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=TeacherActionCallback(lesson_id=lesson_id, action="marks").pack(),
    ))
    return builder.as_markup()
