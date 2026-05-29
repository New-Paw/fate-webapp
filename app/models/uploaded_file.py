from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Identity
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import LargeBinary, Text

from app.db import Base

# A table that defines the information and content of the data files uploaded by users.
class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(start=1),
        primary_key=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    content_type: Mapped[str] = mapped_column(String(255), nullable=True)

    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    usage_type: Mapped[str] = mapped_column(String(32), nullable=False, default="train")

    namespace: Mapped[str] = mapped_column(String(255), nullable=False)

    table_name: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )