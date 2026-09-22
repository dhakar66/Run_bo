from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.activity import Activity
    from models.enrollment import ChallengeEnrollment
    from models.strava_connection import StravaConnection


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    # Auth0's `sub` claim is the stable external identity. No password is stored.
    auth0_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(150))
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    enrollments: Mapped[list[ChallengeEnrollment]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    activities: Mapped[list[Activity]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    strava_connection: Mapped[StravaConnection | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
