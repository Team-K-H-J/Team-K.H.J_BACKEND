from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, BINARY, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Subscribe_log(Base):
    __tablename__ = "subscribe_log"

    id: Mapped[bytes] = mapped_column(
        BINARY(16),
        primary_key=True
    )

    device_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("devices.device_id"),
        nullable=False
    )

    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        ForeignKey("users.user_id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    state: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        server_default="not_subscribed",
    ) 