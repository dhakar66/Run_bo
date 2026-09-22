from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.user import User


class StravaConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strava_connections"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    athlete_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    scopes: Mapped[str] = mapped_column(String(255))
    access_token_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    refresh_token_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="strava_connection")
