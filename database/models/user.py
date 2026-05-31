import enum
from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus"),
        nullable=False,
        server_default=UserStatus.pending.value,
    )
    group_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("groups.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    group: Mapped["Group | None"] = relationship("Group", back_populates="students")
    taught_lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="teacher", foreign_keys="Lesson.teacher_id"
    )
    attendance_records: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="student")
    received_marks: Mapped[list["Mark"]] = relationship(
        "Mark", back_populates="student", foreign_keys="Mark.student_id"
    )
    given_marks: Mapped[list["Mark"]] = relationship(
        "Mark", back_populates="teacher", foreign_keys="Mark.teacher_id"
    )
