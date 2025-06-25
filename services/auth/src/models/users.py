from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy import UUID, String, Integer, DateTime, MetaData, ForeignKey
import uuid
from datetime import datetime, timezone

from src.models.enums import Roles

auth_metadata_obj = MetaData(
    schema='auth',
    naming_convention={
        'ix': 'ix_%(column_0_labe)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    }
)


class Base(DeclarativeBase):
    metadata = auth_metadata_obj


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, unique=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    role: Mapped[list['UserRoles']] = relationship(back_populates='user_id') 


class Roles(Base):
    __tablename__ = 'roles'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, unique=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    user: Mapped[list['UserRoles']] = relationship(back_populates='role_id') 


class UserRoles(Base):
    __tablename__ = 'users_roles'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, unique=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = ForeignKey('users.id', ondelete='CASCADE')
    role_id: Mapped[uuid.UUID] = ForeignKey('roles.id', ondelete='CASCADE')
    
    user: Mapped[User] = relationship(back_populates='role')
    role: Mapped[User] = relationship(back_populates='user')
