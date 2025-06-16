from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column
)
from sqlalchemy import UUID, String, Integer, DateTime
import uuid
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, unique=True)
    username: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
