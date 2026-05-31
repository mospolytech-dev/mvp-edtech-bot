from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.subject import Subject


async def get_all_subjects(session: AsyncSession) -> list[Subject]:
    result = await session.execute(select(Subject).order_by(Subject.name))
    return list(result.scalars().all())


async def create_subject(session: AsyncSession, name: str) -> Subject:
    subject = Subject(name=name)
    session.add(subject)
    await session.flush()
    return subject


async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Subject | None:
    result = await session.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def delete_subject(session: AsyncSession, subject_id: int) -> bool:
    subject = await get_subject_by_id(session, subject_id)
    if not subject:
        return False
    await session.delete(subject)
    await session.flush()
    return True
