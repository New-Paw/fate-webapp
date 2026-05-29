from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Define the table for the prediction record class.
class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1),
        primary_key=True
    )

    prediction_job_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    model_id: Mapped[str] = mapped_column(String(64), nullable=False)

    model_name: Mapped[str] = mapped_column(String(255), nullable=False)

    dataset_file_id: Mapped[int] = mapped_column(Integer, nullable=False)

    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(64), nullable=False, default="SUBMITTED")

    note: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)