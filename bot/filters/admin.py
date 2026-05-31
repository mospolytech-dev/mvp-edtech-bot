from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from bot.config import config


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return user is not None and user.id in config.admin_ids
