from datetime import datetime

from sqlalchemy import ForeignKey, String, BINARY, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime

class Session_Model(Base):
    __tablename__ = "session"

    session_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True
    )

    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        server_default=func.now()
    )

    expired_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False
    )

    purpose: Mapped[str] = mapped_column(String(16), default="login", server_default="login")
    password_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
