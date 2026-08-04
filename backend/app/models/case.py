import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.enums.case_priority import CasePriority
from app.enums.case_status import CaseStatus


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    case_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    client_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    opposing_party: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    court: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=CaseStatus.OPEN.value
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=CasePriority.MEDIUM.value
    )

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="cases"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )