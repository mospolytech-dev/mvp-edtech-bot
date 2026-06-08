from bot.handlers.student.menu import student_router as menu_router
from bot.handlers.student.schedule import student_router as schedule_router
from bot.handlers.student.attendance import student_router as attendance_router
from bot.handlers.student.grades import student_router as grades_router

__all__ = ["menu_router", "schedule_router", "attendance_router", "grades_router"]
