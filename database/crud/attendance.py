from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.attendance import Attendance, AttendanceStatus


async def get_attendance_for_lesson(
    session: AsyncSession,
    lesson_id: int,
    date_: date,
) -> list[Attendance]:
    result = await session.execute(
        select(Attendance).where(
            Attendance.lesson_id == lesson_id,
            Attendance.date == date_,
        )
    )
    return list(result.scalars().all())


async def upsert_attendance(
    session: AsyncSession,
    lesson_id: int,
    student_id: int,
    date_: date,
    status: AttendanceStatus,
) -> Attendance:
    result = await session.execute(
        select(Attendance).where(
            Attendance.lesson_id == lesson_id,
            Attendance.student_id == student_id,
            Attendance.date == date_,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        record = Attendance(
            lesson_id=lesson_id,
            student_id=student_id,
            date=date_,
            status=status,
        )
        session.add(record)
    else:
        record.status = status
    await session.flush()
    return record
