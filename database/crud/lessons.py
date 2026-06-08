from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.lesson import Lesson


async def get_all_lessons(session: AsyncSession) -> list[Lesson]:
    result = await session.execute(
        select(Lesson)
        .options(
            selectinload(Lesson.subject),
            selectinload(Lesson.teacher),
            selectinload(Lesson.group),
        )
        .order_by(Lesson.group_id, Lesson.weekday, Lesson.start_time)
    )
    return list(result.scalars().all())


async def get_lessons_for_teacher(session: AsyncSession, teacher_id: int) -> list[Lesson]:
    result = await session.execute(
        select(Lesson)
        .options(
            selectinload(Lesson.subject),
            selectinload(Lesson.group),
        )
        .where(Lesson.teacher_id == teacher_id)
        .order_by(Lesson.weekday, Lesson.start_time)
    )
    return list(result.scalars().all())


async def get_lesson_by_id(session: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await session.execute(
        select(Lesson)
        .options(
            selectinload(Lesson.subject),
            selectinload(Lesson.group),
            selectinload(Lesson.teacher),
        )
        .where(Lesson.id == lesson_id)
    )
    return result.scalar_one_or_none()


async def create_lesson(
    session: AsyncSession,
    subject_id: int,
    teacher_id: int,
    group_id: int,
    weekday: int,
    start_time: time,
    end_time: time,
    room: str | None,
) -> Lesson:
    lesson = Lesson(
        subject_id=subject_id,
        teacher_id=teacher_id,
        group_id=group_id,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
        room=room,
    )
    session.add(lesson)
    await session.flush()
    return lesson
