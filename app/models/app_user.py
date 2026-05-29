from sqlalchemy import Column, Integer, String, DateTime, Sequence
from sqlalchemy.sql import func

from app.db import Base

# Define the table for Appuser.
class AppUser(Base):
    __tablename__ = "APP_USERS"

    id = Column(
        Integer,
        Sequence("APP_USERS_SEQ"),
        primary_key=True,
        index=True
    )

    account = Column(String(80), unique=True, nullable=False, index=True)

    password_hash = Column(String(255), nullable=False)

    server_username = Column(String(128), nullable=False)

    server_password_encrypted = Column(String(2048), nullable=False)

    is_active = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=False), server_default=func.now())

    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())