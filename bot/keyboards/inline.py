from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule"),
    )
    builder.row(
        InlineKeyboardButton(text="✅ Посещаемость", callback_data="menu:attendance"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Оценки", callback_data="menu:grades"),
    )
    return builder.as_markup()
