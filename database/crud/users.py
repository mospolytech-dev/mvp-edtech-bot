from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.user import User, UserRole, UserStatus


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


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id).options(selectinload(User.group))
    )
    return result.scalar_one_or_none()


async def get_teachers(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.role == UserRole.teacher, User.status == UserStatus.active)
        .order_by(User.full_name)
    )
    return list(result.scalars().all())


async def get_pending_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.status == UserStatus.pending)
        .options(selectinload(User.group))
        .order_by(User.created_at)
    )
    return list(result.scalars().all())


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str,
    role: UserRole,
    group_id: int | None = None,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=role,
        status=UserStatus.pending,
        group_id=group_id,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def update_user_status(
    session: AsyncSession, user_id: int, status: UserStatus
) -> User | None:
    user = await get_user_by_id(session, user_id)
    if user:
        user.status = status
        await session.flush()
    return user
