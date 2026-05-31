import enum
from datetime import date

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("lesson_id", "student_id", "date", name="uq_attendance_lesson_student_date"),)

    lesson_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lessons.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendancestatus"), nullable=False
    )

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="attendance_records")
    student: Mapped["User"] = relationship("User", back_populates="attendance_records")
