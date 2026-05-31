from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Group(Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    students: Mapped[list["User"]] = relationship("User", back_populates="group")
    lessons: Mapped[list["Lesson"]] = relationship("Lesson", back_populates="group")
