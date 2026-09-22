from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.enrollment import ChallengeEnrollment


class ChallengeStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Challenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenges"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="valid_date_range"),
    )

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[ChallengeStatus] = mapped_column(
        Enum(
            ChallengeStatus,
            name="challenge_status",
            values_callable=lambda members: [member.value for member in members],
        ),
        default=ChallengeStatus.DRAFT,
        server_default=ChallengeStatus.DRAFT.value,
    )

    enrollments: Mapped[list[ChallengeEnrollment]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )
