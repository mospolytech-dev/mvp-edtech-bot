from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="subject")
