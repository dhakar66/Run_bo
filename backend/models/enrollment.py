from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.challenge import Challenge
    from models.user import User


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class ChallengeEnrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenge_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_enrollment_user_challenge"),
        CheckConstraint(
            "target_distance_meters IN (50000, 100000)",
            name="valid_target_distance",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), index=True
    )
    target_distance_meters: Mapped[int] = mapped_column(Integer)
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(
            EnrollmentStatus,
            name="enrollment_status",
            values_callable=lambda members: [member.value for member in members],
        ),
        default=EnrollmentStatus.ACTIVE,
        server_default=EnrollmentStatus.ACTIVE.value,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="enrollments")
    challenge: Mapped[Challenge] = relationship(back_populates="enrollments")
