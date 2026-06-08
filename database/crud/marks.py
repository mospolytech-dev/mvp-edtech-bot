from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.lesson import Lesson
from database.models.mark import Mark


async def get_marks_for_student(
    session: AsyncSession,
    student_id: int,
) -> list[Mark]:
    result = await session.execute(
        select(Mark)
        .options(
            selectinload(Mark.lesson).selectinload(Lesson.subject),
        )
        .where(Mark.student_id == student_id)
        .order_by(Mark.created_at.desc())
    )
    return list(result.scalars().all())


async def create_mark(
    session: AsyncSession,
    student_id: int,
    lesson_id: int,
    teacher_id: int,
    value: int,
    comment: str | None = None,
) -> Mark:
    mark = Mark(
        student_id=student_id,
        lesson_id=lesson_id,
        teacher_id=teacher_id,
        value=value,
        comment=comment,
    )
    session.add(mark)
    await session.flush()
    return mark
