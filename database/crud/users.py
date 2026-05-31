from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.user import User, UserStatus


async def get_all_active_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.status == UserStatus.active)
        .options(selectinload(User.group))
        .order_by(User.full_name)
    )
    return list(result.scalars().all())


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id).options(selectinload(User.group))
    )
    return result.scalar_one_or_none()


async def get_teachers(session: AsyncSession) -> list[User]:
    from database.models.user import UserRole
    result = await session.execute(
        select(User)
        .where(User.role == UserRole.teacher, User.status == UserStatus.active)
        .order_by(User.full_name)
    )
    return list(result.scalars().all())
