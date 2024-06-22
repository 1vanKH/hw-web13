from sqlalchemy import create_engine, Column, Integer, String, Boolean, Enum, ForeignKey, DateTime, func, Date
from sqlalchemy.orm import relationship, backref, Mapped
from src.database.db import Base, engine
from datetime import date
import enum

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    birthday = Column(Date)
    extra_data = Column(String, nullable=True)
    created_at: Mapped[date] = Column('created_at', DateTime, default=func.now, nullable=True)
    updated_at: Mapped[date] = Column('updated_at', DateTime, default=func.now, onupdate=func.now,
                                      nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user: Mapped['User'] = relationship('User', backref='contacts', lazy='joined')

class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150))
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    role: Mapped[Enum] = Column('role', Enum(Role), default=Role.user, nullable=True)
    confirmed = Column(Boolean, default=False, nullable=True)

Base.metadata.create_all(bind=engine)
