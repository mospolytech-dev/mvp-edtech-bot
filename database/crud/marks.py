from sqlalchemy.ext.asyncio import AsyncSession

from database.models.mark import Mark


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
