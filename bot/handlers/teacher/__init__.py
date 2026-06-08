from bot.handlers.teacher.menu import teacher_router as menu_router
from bot.handlers.teacher.schedule import teacher_router as schedule_router
from bot.handlers.teacher.attendance import teacher_router as attendance_router
from bot.handlers.teacher.marks import teacher_router as marks_router

__all__ = ["menu_router", "schedule_router", "attendance_router", "marks_router"]
