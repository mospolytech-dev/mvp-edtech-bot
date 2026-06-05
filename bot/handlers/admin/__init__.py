from bot.handlers.admin.applications import applications_router
from bot.handlers.admin.panel import admin_router as panel_router
from bot.handlers.admin.groups import admin_router as groups_router
from bot.handlers.admin.subjects import admin_router as subjects_router
from bot.handlers.admin.schedule import admin_router as schedule_router
from bot.handlers.admin.users import admin_router as users_router

__all__ = [
    "applications_router",
    "panel_router",
    "groups_router",
    "subjects_router",
    "schedule_router",
    "users_router",
]
