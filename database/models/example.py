from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class ExampleModel(Base):
    """
    Placeholder model to verify SQLAlchemy + Alembic setup.
    Replace with real domain models (User, Schedule, Grade, etc.)
    """

    __tablename__ = "example"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
