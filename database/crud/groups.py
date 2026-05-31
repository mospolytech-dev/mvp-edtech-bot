from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.group import Group


async def get_all_groups(session: AsyncSession) -> list[Group]:
    result = await session.execute(select(Group).order_by(Group.name))
    return list(result.scalars().all())


async def get_group_by_id(session: AsyncSession, group_id: int) -> Group | None:
    result = await session.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def create_group(session: AsyncSession, name: str, year: int) -> Group:
    group = Group(name=name, year=year)
    session.add(group)
    await session.flush()
    return group


async def delete_group(session: AsyncSession, group_id: int) -> bool:
    group = await get_group_by_id(session, group_id)
    if not group:
        return False
    await session.delete(group)
    await session.flush()
    return True
