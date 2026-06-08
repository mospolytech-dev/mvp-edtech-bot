from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

WEEKDAYS = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}

ATT_STATUS_LABEL = {
    "present": "✅ Присутствовал",
    "absent": "❌ Отсутствовал",
    "late": "⏰ Опоздал",
    "excused": "📋 Уважительная",
}


def back_to_student_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ В меню", callback_data="student:menu"))
    return builder.as_markup()


def student_menu_back_keyboard() -> InlineKeyboardMarkup:
    return back_to_student_menu()
