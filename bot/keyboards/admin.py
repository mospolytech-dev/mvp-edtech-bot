from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.group import Group
from database.models.lesson import Lesson
from database.models.subject import Subject
from database.models.user import User, UserRole

WEEKDAYS = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}

# (start_hhmm, end_hhmm, label)
TIME_SLOTS: list[tuple[str, str, str]] = [
    ("09:00", "10:30", "1 пара  09:00 – 10:30"),
    ("10:40", "12:10", "2 пара  10:40 – 12:10"),
    ("12:40", "14:10", "3 пара  12:40 – 14:10"),
    ("14:20", "15:50", "4 пара  14:20 – 15:50"),
    ("16:00", "17:30", "5 пара  16:00 – 17:30"),
    ("17:40", "19:10", "6 пара  17:40 – 19:10"),
    ("19:20", "20:50", "7 пара  19:20 – 20:50"),
]
PER_PAGE = 8

ROLE_LABELS = {
    UserRole.student: "Студент",
    UserRole.teacher: "Преподаватель",
    UserRole.admin: "Администратор",
}


class LessonPickCallback(CallbackData, prefix="lp"):
    kind: str   # subject / teacher / group
    value: int


class TimeSlotCallback(CallbackData, prefix="ts"):
    slot: int  # index into TIME_SLOTS


class GroupCallback(CallbackData, prefix="grp"):
    action: str   # delete / confirm
    group_id: int


class SubjectCallback(CallbackData, prefix="subj"):
    action: str   # delete / confirm
    subject_id: int


class PageCallback(CallbackData, prefix="pg"):
    section: str  # groups / subjects
    page: int


class ApplicationCallback(CallbackData, prefix="app"):
    action: str   # approve / reject
    user_id: int


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="adm:users"),
        InlineKeyboardButton(text="📋 Заявки", callback_data="adm:applications"),
    )
    builder.row(
        InlineKeyboardButton(text="🏫 Группы", callback_data="adm:groups"),
        InlineKeyboardButton(text="📚 Дисциплины", callback_data="adm:subjects"),
    )
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="adm:schedule"))
    return builder.as_markup()


def application_review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=ApplicationCallback(action="approve", user_id=user_id).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=ApplicationCallback(action="reject", user_id=user_id).pack(),
        ),
    )
    return builder.as_markup()


def applications_list_keyboard(users: list[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for u in users:
        builder.row(InlineKeyboardButton(
            text=f"👤 {u.full_name}",
            callback_data=ApplicationCallback(action="view", user_id=u.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:menu"))
    return builder.as_markup()


def application_detail_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=ApplicationCallback(action="approve", user_id=user_id).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=ApplicationCallback(action="reject", user_id=user_id).pack(),
        ),
    )
    builder.row(InlineKeyboardButton(text="⬅️ К списку заявок", callback_data="adm:applications"))
    return builder.as_markup()


def back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="adm:menu"))
    return builder.as_markup()


def _pagination_row(builder: InlineKeyboardBuilder, section: str, page: int, total: int) -> None:
    if total <= PER_PAGE:
        return
    total_pages = (total - 1) // PER_PAGE + 1
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀️", callback_data=PageCallback(section=section, page=page - 1).pack()
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1} / {total_pages}", callback_data="adm:noop"))
    if (page + 1) * PER_PAGE < total:
        nav.append(InlineKeyboardButton(
            text="▶️", callback_data=PageCallback(section=section, page=page + 1).pack()
        ))
    builder.row(*nav)


def groups_keyboard(groups: list[Group], page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_items = groups[page * PER_PAGE: (page + 1) * PER_PAGE]
    for g in page_items:
        builder.row(
            InlineKeyboardButton(text=f"{g.name} ({g.year})", callback_data="adm:noop"),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=GroupCallback(action="delete", group_id=g.id).pack(),
            ),
        )
    _pagination_row(builder, "groups", page, len(groups))
    builder.row(InlineKeyboardButton(text="➕ Создать группу", callback_data="adm:groups:add"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:menu"))
    return builder.as_markup()


def confirm_delete_group_keyboard(group_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=GroupCallback(action="confirm", group_id=group_id).pack(),
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="adm:groups"),
    )
    return builder.as_markup()


def subjects_keyboard(subjects: list[Subject], page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_items = subjects[page * PER_PAGE: (page + 1) * PER_PAGE]
    for s in page_items:
        builder.row(
            InlineKeyboardButton(text=s.name, callback_data="adm:noop"),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=SubjectCallback(action="delete", subject_id=s.id).pack(),
            ),
        )
    _pagination_row(builder, "subjects", page, len(subjects))
    builder.row(InlineKeyboardButton(text="➕ Создать дисциплину", callback_data="adm:subjects:add"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:menu"))
    return builder.as_markup()


def confirm_delete_subject_keyboard(subject_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=SubjectCallback(action="confirm", subject_id=subject_id).pack(),
        ),
        InlineKeyboardButton(text="❌ Отмена", callback_data="adm:subjects"),
    )
    return builder.as_markup()


def schedule_keyboard(lessons: list[Lesson]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Добавить занятие", callback_data="adm:schedule:add"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:menu"))
    return builder.as_markup()


def pick_subject_keyboard(subjects: list[Subject]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in subjects:
        builder.row(InlineKeyboardButton(
            text=s.name,
            callback_data=LessonPickCallback(kind="subject", value=s.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))
    return builder.as_markup()


def pick_teacher_keyboard(teachers: list[User]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in teachers:
        builder.row(InlineKeyboardButton(
            text=t.full_name,
            callback_data=LessonPickCallback(kind="teacher", value=t.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))
    return builder.as_markup()


def pick_group_keyboard(groups: list[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in groups:
        builder.row(InlineKeyboardButton(
            text=f"{g.name} ({g.year})",
            callback_data=LessonPickCallback(kind="group", value=g.id).pack(),
        ))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))
    return builder.as_markup()


def pick_time_slot_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, (_, _, label) in enumerate(TIME_SLOTS):
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=TimeSlotCallback(slot=i).pack(),
        ))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))
    return builder.as_markup()
