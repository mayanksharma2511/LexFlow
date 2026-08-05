import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.enums.document_type import DocumentType


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
        default=DocumentType.OTHER,
    )

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id"),
        nullable=False,
    )

    case = relationship(
        "Case",
        back_populates="documents",
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )