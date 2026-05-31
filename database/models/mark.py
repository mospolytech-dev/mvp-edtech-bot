from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Mark(Base):
    __tablename__ = "marks"
    __table_args__ = (CheckConstraint("value BETWEEN 1 AND 5", name="ck_mark_value_range"),)

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("lessons.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    student: Mapped["User"] = relationship("User", back_populates="received_marks", foreign_keys=[student_id])
    teacher: Mapped["User"] = relationship("User", back_populates="given_marks", foreign_keys=[teacher_id])
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="marks")
