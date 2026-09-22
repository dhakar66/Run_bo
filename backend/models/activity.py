from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.user import User


class ActivitySource(str, enum.Enum):
    STRAVA = "strava"
    MANUAL = "manual"


class Activity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint(
            "source", "external_activity_id", name="uq_activity_source_external_id"
        ),
        CheckConstraint("distance_meters > 0", name="positive_distance"),
        CheckConstraint("moving_time_seconds >= 0", name="nonnegative_moving_time"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[ActivitySource] = mapped_column(
        Enum(
            ActivitySource,
            name="activity_source",
            values_callable=lambda members: [member.value for member in members],
        ),
        index=True,
    )
    external_activity_id: Mapped[str | None] = mapped_column(String(255))
    activity_type: Mapped[str] = mapped_column(String(50), default="run")
    name: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    distance_meters: Mapped[int] = mapped_column(BigInteger)
    moving_time_seconds: Mapped[int] = mapped_column(Integer)
    is_eligible: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", index=True
    )
    exclusion_reason: Mapped[str | None] = mapped_column(String(255))
    source_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    user: Mapped[User] = relationship(back_populates="activities")
