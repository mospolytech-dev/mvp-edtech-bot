from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.users import get_user_by_telegram_id
from database.models.user import UserRole, UserStatus


class IsStudent(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        session: AsyncSession,
    ) -> bool | dict:
        tg_user = event.from_user
        if tg_user is None:
            return False
        user = await get_user_by_telegram_id(session, tg_user.id)
        if user is None:
            return False
        if user.role == UserRole.student and user.status == UserStatus.active:
            return {"student": user}
        return False
