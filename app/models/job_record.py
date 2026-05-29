from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Identity
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# It defines the model for training/prediction task record table.
class JobRecord(Base):
    __tablename__ = "job_records"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1),
        primary_key=True
    )

    job_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    job_type: Mapped[str] = mapped_column(String(32), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=True)

    role: Mapped[str] = mapped_column(String(32), nullable=False, default="guest")

    party_id: Mapped[str] = mapped_column(String(32), nullable=False, default="9999")

    status: Mapped[str] = mapped_column(String(64), nullable=False, default="SUBMITTED")

    source_script: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)