from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Define the table for the trained model.
class ModelRecord(Base):
    __tablename__ = "model_records"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1),
        primary_key=True
    )

    model_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    algorithm: Mapped[str] = mapped_column(String(128), nullable=False)

    version: Mapped[str] = mapped_column(String(64), nullable=False, default="v1.0")

    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)