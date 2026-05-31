from datetime import time

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1=Mon … 7=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(50), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="lessons")
    teacher: Mapped["User"] = relationship("User", back_populates="taught_lessons", foreign_keys=[teacher_id])
    group: Mapped["Group"] = relationship("Group", back_populates="lessons")
    attendance_records: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="lesson")
    marks: Mapped[list["Mark"]] = relationship("Mark", back_populates="lesson")
