from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.group import Group
from database.models.subject import Subject

REG_PER_PAGE = 8


class RegRoleCallback(CallbackData, prefix="reg_role"):
    role: str


class RegGroupCallback(CallbackData, prefix="reg_grp"):
    group_id: int


class RegGroupPageCallback(CallbackData, prefix="reg_grp_pg"):
    page: int


class RegSubjectCallback(CallbackData, prefix="reg_subj"):
    subject_id: int
    page: int


class RegSubjectPageCallback(CallbackData, prefix="reg_subj_pg"):
    page: int


def role_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="👨‍🎓 Студент",
        callback_data=RegRoleCallback(role="student").pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="👨‍🏫 Преподаватель",
        callback_data=RegRoleCallback(role="teacher").pack(),
    ))
    builder.row(InlineKeyboardButton(
        text="👨‍💼 Администратор",
        callback_data=RegRoleCallback(role="admin").pack(),
    ))
    return builder.as_markup()


def _pagination_row(
    builder: InlineKeyboardBuilder,
    page_callback_cls,
    page: int,
    total: int,
) -> None:
    if total <= REG_PER_PAGE:
        return
    total_pages = (total - 1) // REG_PER_PAGE + 1
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀️",
            callback_data=page_callback_cls(page=page - 1).pack(),
        ))
    nav.append(InlineKeyboardButton(
        text=f"{page + 1} / {total_pages}",
        callback_data="reg:noop",
    ))
    if (page + 1) * REG_PER_PAGE < total:
        nav.append(InlineKeyboardButton(
            text="▶️",
            callback_data=page_callback_cls(page=page + 1).pack(),
        ))
    builder.row(*nav)


def group_selection_keyboard(groups: list[Group], page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_items = groups[page * REG_PER_PAGE: (page + 1) * REG_PER_PAGE]
    row: list[InlineKeyboardButton] = []
    for g in page_items:
        row.append(InlineKeyboardButton(
            text=f"{g.name} ({g.year})",
            callback_data=RegGroupCallback(group_id=g.id).pack(),
        ))
        if len(row) == 2:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    _pagination_row(builder, RegGroupPageCallback, page, len(groups))
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=RegGroupCallback(group_id=0).pack(),
    ))
    return builder.as_markup()


def subject_selection_keyboard(
    subjects: list[Subject],
    selected_ids: set[int],
    page: int = 0,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    page_items = subjects[page * REG_PER_PAGE: (page + 1) * REG_PER_PAGE]
    row: list[InlineKeyboardButton] = []
    for s in page_items:
        prefix = "✅ " if s.id in selected_ids else ""
        row.append(InlineKeyboardButton(
            text=f"{prefix}{s.name}",
            callback_data=RegSubjectCallback(subject_id=s.id, page=page).pack(),
        ))
        if len(row) == 2:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    _pagination_row(builder, RegSubjectPageCallback, page, len(subjects))
    count = len(selected_ids)
    done_text = f"✅ Готово — выбрано {count}" if count else "⏭ Пропустить"
    builder.row(InlineKeyboardButton(text=done_text, callback_data="reg:subjects_done"))
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule"))
    builder.row(InlineKeyboardButton(text="✅ Посещаемость", callback_data="menu:attendance"))
    builder.row(InlineKeyboardButton(text="📊 Оценки", callback_data="menu:grades"))
    return builder.as_markup()
