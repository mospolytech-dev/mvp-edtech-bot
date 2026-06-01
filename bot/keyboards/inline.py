from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.group import Group


class RegRoleCallback(CallbackData, prefix="reg_role"):
    role: str


class RegGroupCallback(CallbackData, prefix="reg_grp"):
    group_id: int


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


def group_selection_keyboard(groups: list[Group]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for g in groups:
        builder.row(InlineKeyboardButton(
            text=f"{g.name} ({g.year})",
            callback_data=RegGroupCallback(group_id=g.id).pack(),
        ))
    builder.row(InlineKeyboardButton(
        text="⏭ Пропустить",
        callback_data=RegGroupCallback(group_id=0).pack(),
    ))
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule"))
    builder.row(InlineKeyboardButton(text="✅ Посещаемость", callback_data="menu:attendance"))
    builder.row(InlineKeyboardButton(text="📊 Оценки", callback_data="menu:grades"))
    return builder.as_markup()
